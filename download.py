import glob
import os
import requests
import gzip

# 実行
files = glob.glob('Tenhou/Research/log/鳳凰卓/**/*.csv')
for file in files:
    dir = os.path.splitext(os.path.basename(file))[0]
    paifu = []
    with open(file, encoding='utf-8') as f:
        paifu = f.read().splitlines()
    for i in range(len(paifu)):
        id = paifu[i][26:57]
        tw = paifu[i][57:]
        res = requests.get('https://tenhou.net/0/log/?' + id).text
        with gzip.open('Tenhou/Research/log/鳳凰卓/' + dir + '/' + id + tw + '.mjlog', 'wt', encoding='utf_8') as g:
            g.writelines(res)
print('done')
