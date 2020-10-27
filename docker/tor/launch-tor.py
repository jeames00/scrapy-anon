import socket, os, logging, grpc, subprocess

from concurrent import futures
import stem.process

import launchtor_pb2, launchtor_pb2_grpc
import scrapyanon.secrets as secrets

hashed_tor_ctrl_pwd = subprocess.run(
    ["tor", "--hash-password", secrets.TOR_CONTROL_PASSWORD],
    encoding='utf-8',
    capture_output=True
).stdout
#hashed_tor_ctrl_pwd = os.environ["HASHED_TOR_CONTROL_PASSWORD"]
tor_grpc_port = os.environ["TOR_GRPC_PORT"]


class TorRequester(launchtor_pb2_grpc.TorRequesterServicer):

    def RequestLaunch(self, request, context):
        try:
            tor_process = stem.process.launch_tor_with_config(
                config = {
                    'ControlPort': '0.0.0.0:'+str(request.controlPort),
                    'SOCKSPort': '0.0.0.0:'+str(request.socksPort),
                    'DataDirectory': '/home/tor/.tor/custom_socks_'+str(request.socksPort),
                    'HashedControlPassword': hashed_tor_ctrl_pwd,
                    'HTTPTunnelPort': '0.0.0.0:auto',
                    'Log': [
                        'NOTICE stdout',
                        'ERR file /home/tor/tor_error_log_'+str(request.socksPort),
                    ],
                },
            )
            return launchtor_pb2.LaunchReply(success=True)
        except OSError:
            return launchtor_pb2.LaunchReply(success=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    launchtor_pb2_grpc.add_TorRequesterServicer_to_server(TorRequester(), server)
    server.add_insecure_port('[::]:'+tor_grpc_port)
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()
        
