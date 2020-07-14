import sys
sys.path.insert(0, './Sublist3r')
import sublist3r
import argparse
import os
from selenium import webdriver
from multiprocessing import Process, Queue

t_dir = ''

def get_subs(domain, threads):
    return sublist3r.main(domain, threads, None, ports=None, silent=False, verbose= False, enable_bruteforce= False, engines=None)

def save_screen(queue):
    global t_dir
    fireFoxOptions = webdriver.FirefoxOptions()
    fireFoxOptions.set_headless()
    driver = webdriver.Firefox(firefox_options=fireFoxOptions)
    driver.maximize_window()
    while not queue.empty():
        url = queue.get(block=False)
        print("Scraping " + url)
        try:
            driver.get(url)
        except Exception:
            continue
        file_name = t_dir + os.sep + url.replace('://', '_').replace('/','_').replace(':', '_').replace('?', '_').replace('#','_').replace('&','_') + '.png'
        driver.save_screenshot(file_name)
    driver.close()

def parse_args(argv):
    parser = argparse.ArgumentParser(description='Scraper for subdomain lists.')
    parser.add_argument('--domain', dest='domain', action='store', help='Base domain to use with Sublist3r.', default=None)
    parser.add_argument('--url_list', dest='url_list', action='store', help='Use a text file with urls instead.', default=None)
    parser.add_argument('--threads', dest='threads', action='store', help='Concurrent threads to run. (Default: 2)', default=2, type=int)
    parser.add_argument('--ports', dest='ports', action='store', help='Comma separated ports to use with sublist3r and the scraper. (Default: 80,443)', default='80,443')
    parser.add_argument('--dir', dest='dir', action='store', help='Target directory for screenshots. (Default: ./screens)', default='./screens')
    if(len(argv) == 1):
        args = parser.parse_args(['-h'])
        sys.exit(1)
    else:
        args = parser.parse_args(argv[1:])
    if(args.domain is None and args.url_list is None):
        print('Please supply a domain or an url list file.\n')
        sys.exit(1)
    return args

def check_target_dir(directory):
    global t_dir
    t_dir = directory
    if(os.path.exists(directory)):
        if(os.path.isdir(directory)):
            return True
        else:
            print('Target directory is a file.')
            return False
    try:
        os.mkdir(directory)
        print('Created directory ' + directory)
        return True
    except Exception as e:
        print('Error creating directory: ' + str(e))
        return False

def load_from_file(file):
    print('Loading subdomains from file ' + file)
    try: 
        with open(file) as fp:
            data = fp.read().splitlines()
    except Exception as e:
        print('Error opening url file: ' + str(e))
        sys.exit(1)
    return data

if __name__ == '__main__':
    queue = Queue()
    args = parse_args(sys.argv)
    if(not check_target_dir(args.dir)):
        sys.exit(1)
    if(args.domain is None):
        subs = load_from_file(args.url_list)
    else:
        subs = get_subs(args.domain, args.threads)
    for sub in subs:
        for port in args.ports.split(','):
            queue.put('http://' + sub + ':' + port)
            queue.put('https://' + sub + ':' + port)
    print('Starting subdomain scraping with ' + str(args.threads) + ' threads...')
    for i in range(args.threads):
        p = Process(target=save_screen, args=(queue,))
        p.start()