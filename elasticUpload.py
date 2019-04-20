from elasticsearch_dsl import Search
import elasticsearch, json, requests, argparse, sys

from elasticsearch import Elasticsearch

p = argparse.ArgumentParser()
p.add_argument('i', metavar='input', type=str, help='Upload or delete instruction')
p.add_argument('idx', metavar='index', type=str, help='Index of the table to upload/delete') # events o tweets
args = p.parse_args()

if args.idx != 'events' and args.idx != 'tweets':
    print('Solo hay dos indices de tablas posibles: "events" o "tweets"')
    sys.exit()
elif args.idx == 'events':
    datafile = 'detected_events.txt'
else:
    datafile = 'tweets.txt'

def upload(index):
    es = Elasticsearch(hosts='http://localhost:9200')

    with open(datafile,'r') as file:
        for line in file:
            doc=json.loads(line)
            if args.idx.lower() == 'events':
                res = es.index(index=index, id=doc['id'], doc_type='event', body=doc)
            else:
                res = es.index(index=index, doc_type='tweet', body=doc)
            if (res['result']!='created'):
                print(res['result'])

def delete(index):
    es = Elasticsearch(hosts='http://localhost:9200')

    es.indices.delete(index=index, ignore=[400, 404])

if __name__ == '__main__':
    if args.i.lower() == 'upload':
        upload(args.idx)
    elif args.i.lower() == 'delete':
        delete(args.idx)
