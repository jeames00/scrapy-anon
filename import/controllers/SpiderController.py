import json, os, requests, os, importlib, pathlib

class SpiderController:

    def __init__(self, *args):
        self.scrapy_project = os.environ["SCRAPY_PROJECT"]

    # Returns list of tuples: [(spider name, number of categories), ...]
    def get_spider_list(self):
        scrapy_project = os.environ["SCRAPY_PROJECT"]
        response = requests.get(
            'http://scrapy:'+os.environ["SCRAPYD_PORT"]+'/listspiders.json',
            {'project': self.scrapy_project}
        )
        spider_list = [s for s in json.loads(response.text)['spiders'] if s[0] != '_']
        spider_num_of_categories = []
    #    for spider in spider_list:
    #        file_path = scrapy_project+'/'+scrapy_project+'/spiders/'+spider + '.py'
    #        module_name = spider
    #        spec = importlib.util.spec_from_file_location(module_name, file_path)
    #        module = importlib.util.module_from_spec(spec)
    #        spec.loader.exec_module(module)
    #        spider_num_of_categories.append(module.sports_num)

        return list(zip(spider_list))
    #    return list(zip(spider_list, spider_num_of_categories))

    # Request scrapyd to run spiders
    def launch_spiders(self, spiders_to_crawl, proxy_tuples, client_hello_json):
        proxies = [x[0] for x in proxy_tuples]
        exit_ips = [x[1] for x in proxy_tuples]
        
        if len(spiders_to_crawl) == 0:
            print("no spiders to crawl, next exit node...")
            return
        
        for spider in spiders_to_crawl:
            print("crawling " + spider + " spider...")
            proxies = ','.join(proxies)
            exit_ips = ','.join(exit_ips)
            data = [
               ('project', self.scrapy_project),
               ('spider', spider),
               ('setting','ROBOTSTXT_OBEY=False'),
               ('client_hello', client_hello_json),
               ('proxies', proxies),
               ('exit_ips', exit_ips),
               ('crawl_type', 'check_tor_exit')
            ]
            response = requests.post('http://localhost:6800/schedule.json', data=data)
            print(response.text)
