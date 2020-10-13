package main

import (
	"encoding/json"
	utls "github.com/refraction-networking/utls"
	"log"
	"math/rand"
	"time"
)

var GREASEvalues []uint16 = []uint16{
	0x0A0A, 0x1A1A, 0x2A2A, 0x3A3A, 0x4A4A, 0x5A5A, 0x6A6A, 0x7A7A, 0x8A8A, 0x9A9A, 0xAAAA, 0xBABA, 0xCACA, 0xDADA, 0xEAEA, 0xFAFA}
var GREASEPSKKeyExchangeModes []uint8 = []uint8{0x0B, 0x2A, 0x49, 0x68, 0x87, 0xA6, 0xC5, 0xE4}
var serverHost string

type TLSExtensionAttributes struct {
	CipherSuites        []uint16 `json:"cipher_suites"`
	CompressionMethods  []uint8  `json:"compression_methods"`
	Extensions          []uint16 `json:"extensions"`
	ElipticCurves       []uint16 `json:"supported_groups"`
	ECPointFormats      []uint8  `json:"supported_points"`
	KeyShareEntries     []uint16 `json:"key_share_entries"`
	SignatureAlgorithms []uint16 `json:"signature_algorithms"`
	SupportedVersions   []uint16 `json:"supported_versions"`
	PSKKeyExchangeModes []uint8  `json:"psk_key_exchange_modes"`
	ALPNs               []string `json:"alpns"`
	CompressCertificate []uint16 `json:"compress_certificate"`
	RecordSizeLimit     uint16   `json:"record_size_limit"`
}

func isGREASEvalue(val uint16) bool {
	for _, x := range GREASEvalues {
		if x == val {
			return true
		}
	}
	return false
}

func isGREASEPSKKeyExchangeMode(val uint8) bool {
	for _, x := range GREASEPSKKeyExchangeModes {
		if x == val {
			return true
		}
	}
	return false
}

func buildClientHelloSpec(tlsea *TLSExtensionAttributes) *utls.ClientHelloSpec {
	chs := &utls.ClientHelloSpec{
		CipherSuites:       nil,
		CompressionMethods: nil,
		Extensions:         nil,
		GetSessionID:       nil,
	}

	if len(tlsea.CipherSuites) != 0 {
		chs.CipherSuites = make([]uint16, len(tlsea.CipherSuites))
		for i, x := range tlsea.CipherSuites {
			if isGREASEvalue(x) {
				x = utls.GREASE_PLACEHOLDER
			}
			chs.CipherSuites[i] = x
		}
	}

	if len(tlsea.CompressionMethods) != 0 {
		chs.CompressionMethods = tlsea.CompressionMethods
	}

	if len(tlsea.Extensions) != 0 {
		chs.Extensions = make([]utls.TLSExtension, len(tlsea.Extensions))
		for i, extensionVal := range tlsea.Extensions {
			switch extensionVal {
			case 0:
				chs.Extensions[i] = &utls.SNIExtension{
					ServerName: serverHost,
				}
			case 5:
				chs.Extensions[i] = &utls.StatusRequestExtension{}
			case 10:
				a := []utls.CurveID{}
				for _, x := range tlsea.ElipticCurves {
					if isGREASEvalue(x) {
						x = utls.GREASE_PLACEHOLDER
					}
					a = append(a, utls.CurveID(x))
				}

				chs.Extensions[i] = &utls.SupportedCurvesExtension{a}
			case 11:
				chs.Extensions[i] = &utls.SupportedPointsExtension{
					SupportedPoints: tlsea.ECPointFormats,
				}
			case 13:
				a := []utls.SignatureScheme{}
				for _, x := range tlsea.SignatureAlgorithms {
					a = append(a, utls.SignatureScheme(x))
				}

				chs.Extensions[i] = &utls.SignatureAlgorithmsExtension{
					SupportedSignatureAlgorithms: a,
				}
			case 16:
				chs.Extensions[i] = &utls.ALPNExtension{
					AlpnProtocols: tlsea.ALPNs,
				}
			case 18:
				chs.Extensions[i] = &utls.SCTExtension{}
			case 21:
				chs.Extensions[i] = &utls.UtlsPaddingExtension{
					GetPaddingLen: utls.BoringPaddingStyle,
				}
			case 23:
				chs.Extensions[i] = &utls.UtlsExtendedMasterSecretExtension{}
			case 27:
				a := []utls.CertCompressionAlgo{}
				for _, x := range tlsea.CompressCertificate {
					a = append(a, utls.CertCompressionAlgo(x))
				}

				chs.Extensions[i] = &utls.FakeCertCompressionAlgsExtension{a}

			case 28:
				chs.Extensions[i] = &utls.FakeRecordSizeLimitExtension{
					Limit: tlsea.RecordSizeLimit,
				}
			case 35:
				chs.Extensions[i] = &utls.SessionTicketExtension{}
			case 43:
				for j, x := range tlsea.SupportedVersions {
					if isGREASEvalue(x) {
						tlsea.SupportedVersions[j] = utls.GREASE_PLACEHOLDER
					}
				}

				chs.Extensions[i] = &utls.SupportedVersionsExtension{
					tlsea.SupportedVersions,
				}
			case 45:
				chs.Extensions[i] = &utls.PSKKeyExchangeModesExtension{
					tlsea.PSKKeyExchangeModes,
				}
			case 51:
				a := []utls.KeyShare{}
				for j, x := range tlsea.KeyShareEntries {
					k := utls.KeyShare{}
					if isGREASEvalue(x) {
						x = utls.GREASE_PLACEHOLDER
					}
					k.Group = utls.CurveID(x)
					if j == 0 {
						k.Data = []byte{0}
					}
					a = append(a, k)
				}

				chs.Extensions[i] = &utls.KeyShareExtension{
					KeyShares: a,
				}
			case 65281:
				chs.Extensions[i] = &utls.RenegotiationInfoExtension{}
			default:
				if isGREASEvalue(extensionVal) {
					chs.Extensions[i] = &utls.UtlsGREASEExtension{}
				} else {
					log.Fatalf("Error: tried to unmarshal unsupported TLS extension number %d", extensionVal)
				}
			}
		}

	}
	return chs
}

func getClientHelloSpec(clientHello, host string) *utls.ClientHelloSpec {
	var t TLSExtensionAttributes
	serverHost = host

	if err := json.Unmarshal([]byte(clientHello), &t); err != nil {
		log.Fatal(err)
	}

	if t.PSKKeyExchangeModes != nil {
		for i, x := range t.PSKKeyExchangeModes {
			if isGREASEPSKKeyExchangeMode(x) {
				s := rand.NewSource(time.Now().UnixNano())
				r := rand.New(s)
				t.PSKKeyExchangeModes[i] = GREASEPSKKeyExchangeModes[r.Intn(
					len(GREASEPSKKeyExchangeModes))]
			}
		}

	}

	clientHelloSpec := buildClientHelloSpec(&t)
	return clientHelloSpec
}
