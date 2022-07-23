import glob
import binascii
import gzip
import os
import re
import csv

# 条件
lobbyIn = 0
playernumIn = 4
playerlevelIn = 3
playlengthIn = 2
kuitanariIn = 1
akaariIn = 1
sokutakuIn = 0

# プレーヤー名をパーセントエンコード
def encodePer(name):
    hex = str.upper(str(binascii.hexlify(name.encode('utf-8')))[2:-1])
    before = list(hex)
    after = []
    for i in range(len(before) // 2):
        after.append('%')
        after.append(before[2 * i])
        after.append(before[2 * i + 1])
    namePer = ''.join(after)
    return namePer

# 席順を判定
def judgeTw(file, xml, namePer):
    twUrl = None
    twXml = None
    tw = None # 席順 (0=東家, 1=南家, 2=西家, 3=北家)
    try:
        twUrl = os.path.splitext(os.path.basename(file))[0][-1]
    except:
        pass
    try:
        twXml = xml[xml.find(namePer) - 3]
    except:
        pass
    if twUrl == '0' or twUrl == '1' or twUrl == '2' or twUrl == '3':
        tw = int(twUrl)
    else:
        if twXml == '0' or twXml == '1' or twXml == '2' or twXml == '3':
            tw = int(twXml)
    return tw

# ルールを判定
def judgeRules(xml):
    try:
        lobby = int(re.search(r'lobby=\"[0-9]+\"', xml).group()[7:-1]) # ロビー(0=段位戦)
    except:
        lobby = 0
    num = int(re.search(r'type=\"[0-9]+\"', xml).group()[6:-1])
    bin = format(num, 'b')
    playernum = None # 人数 (4=四麻, 3=三麻)
    try:
        if bin[-5] == '0':
            playernum = 4
        else:
            playernum = 3
    except:
        pass
    playerlevel = None # 卓 (3=鳳凰卓, 2=特上卓, 1=上級卓, 0=一般卓)
    try:
        if bin[-6] == '1' and bin[-8] == '1':
            playerlevel = 3
        else:
            if bin[-6] == '1':
                playerlevel = 2
            elif bin[-8] == '1':
                playerlevel = 1
            else:
                playerlevel = 0
    except:
        pass
    playlength = None # 長さ (2=東南戦, 1=東風戦)
    try:
        if bin[-4] == '1':
            playlength = 2
        else:
            playlength = 1
    except:
        pass
    kuitanari = None # 喰タン (1=喰アリ, 0=喰ナシ)
    try:
        if bin[-3] == '0':
            kuitanari = 1
        else:
            kuitanari = 0
    except:
        pass
    akaari = None # 赤ドラ (1=赤アリ, 0=赤ナシ)
    try:
        if bin[-2] == '0':
            akaari = 1
        else:
            akaari = 0
    except:
        pass
    sokutaku = None # 速さ (1=速卓, 0=通常卓)
    try:
        if bin[-7] == '1':
            sokutaku = 1
        else:
            sokutaku = 0
    except:
        pass
    rules = [lobby, playernum, playerlevel, playlength, kuitanari, akaari, sokutaku]
    return rules

# レートを計算
def calcRates(xml, tw):
    array = re.search(r'rate=\"[0-9,.]+\"', xml).group()[6:-1].split(',')
    array = [float(i) for i in array]
    rate = array[tw] # プレーヤーレート
    rateTaku = float(format(sum([i for i in array]) / len(array), '.4f'))
    rates = [rate, rateTaku]
    return rates

# 結果を判定
def calcResults(xml, tw):
    array = re.search(r'owari=\"[0-9,.-]+\"', xml).group()[7:-1].replace('.0', '').split(',')
    array = [float(i) for i in array]
    soten = int(array[tw * 2] * 100) # 素点
    score = array[tw * 2 + 1] # スコア
    arrayScore = []
    for i in range(len(array) // 2):
        arrayScore.append(array[i * 2 + 1])
    rank = 0 # 順位
    for i in range(len(arrayScore)):
        if arrayScore[tw] <= arrayScore[i]:
            rank += 1
    results = [soten, score, rank]
    return results

# ゲームデータを取得
def getGame(xml, id, tw):
    rules = judgeRules(xml) # ルール
    dan = int(re.search(r'dan=\"[0-9,]+\"', xml).group()[5:-1].split(',')[tw]) # 段位(0=新人, 1～9=9級～1級, 10～19=初段～十段, 20=天鳳位)
    rates = calcRates(xml, tw) # レート
    results = calcResults(xml, tw) # 結果
    game = [id, tw] + rules + [dan] + rates + results
    return game

# 親子を判定
def judgeOya(init, tw):
    oyaPlayer = int(re.search(r'oya=\"[0-9]\"', init).group()[5:6]) # 親 (0～3=起家～ラス親)
    if oyaPlayer == tw:
        oya = 1
    else:
        oya = 0
    return oya

# ダブロンを判定
def judgeDouble(init):
    if init.count('AGARI') >= 2:
        double = init.count('AGARI') - 1
    else:
        double = 0
    return double

# 和了者を判定
def judgeHora(init):
    horaArray = re.findall(r'who=\"[0-9]\" fromWho=\"[0-9]\"', init)
    horaArray = [int(i[5:6]) for i in horaArray]
    return horaArray

# 放銃者を判定
def judgeHojyu(init):
    hojyuArray = re.findall(r'who=\"[0-9]\" fromWho=\"[0-9]\"', init)
    hojyuArray = [int(i[17:18]) for i in hojyuArray]
    return hojyuArray

# 席順からツモ牌・打牌記号を判定
def judgePlayerSign(tw):
    signTsumo = None
    signDa = None
    if tw == 0:
        signTsumo = 'T'
        signDa = 'D'
    elif tw == 1:
        signTsumo = 'U'
        signDa = 'E'
    elif tw == 2:
        signTsumo = 'V'
        signDa = 'F'
    elif tw == 3:
        signTsumo = 'W'
        signDa = 'G'
    sign = [signTsumo, signDa]
    return sign

# 鳴きを判定
def judgeNaki(num):
    bin = format(num, 'b')
    naki = None
    try:
        if bin[-3] == '1':
            naki = 0 # チー
        else:
            if bin[-4] == '1':
                naki = 1 # ポン
            else:
                if bin[-5] == '1':
                    naki = 2 # 加カン
                else:
                    if bin[-6] == '1':
                        naki = 3 # 北抜き
                    else:
                        if bin[-1] == '0':
                            naki = 4 # アンカン
                        else:
                            naki = 5 # ダイミンカン
    except:
        if bin[-1] == '0':
            naki = 4 # アンカン
        else:
            naki = 5 # ダイミンカン
    return naki

# リーチ・フーロ巡目を計算
def calcSengen(init, tw):
    signTsumo = judgePlayerSign(tw)[0]
    array = init.split('/><')
    jyunSengen = 0
    for i in range(len(array)):
        resReach = re.search(r'REACH who=\"' + str(tw) + r'\"', array[i])
        resFuro = re.search(r'N who=\"' + str(tw) + r'\" m=\"[0-9]+\"', array[i]) # アヤシイ
        # リーチ
        if resReach:
            break
        # フーロ
        elif resFuro:
            resFuro = int(resFuro.group()[13:-1])
            naki = judgeNaki(resFuro)
            # チー・ポン・ダイミンカン
            if naki == 0 or naki == 1 or naki == 5:
                break
        res = re.search(signTsumo + r'[0-9]+', array[i])
        if res:
            jyunSengen += 1
    return jyunSengen

# 和了・放銃巡目を計算
def calcAgari(init, tw):
    signTsumo = judgePlayerSign(tw)[0]
    array = init.split('/><')
    jyunAgari = 0
    for i in range(len(array)):
        res = re.search(signTsumo + r'[0-9]+', array[i])
        if res:
            jyunAgari += 1
    return jyunAgari

# 局の結果を判定
def judgeKekka(init, tw, double, horaArray, hojyuArray):
    kekka = None
    # アガりの場合
    if 'AGARI' in init:
        if double == 0:
            hora = int(re.search(r'who=\"[0-9]\" fromWho=\"[0-9]\"', init).group()[5:6]) # 和了者 (0=東家, 1=南家, 2=西家, 3=北家)
            hojyu = int(re.search(r'who=\"[0-9]\" fromWho=\"[0-9]\"', init).group()[17:18]) # 放銃者 (0=東家, 1=南家, 2=西家, 3=北家) (和了者と同じときはツモ)
            if hora == tw and hora == hojyu:
                kekka = 0 # ツモ
            elif hora == tw and hora != hojyu:
                kekka = 1 # ロン
            elif hojyu == tw:
                kekka = 2 # 放銃
            elif hora != tw and hora == hojyu:
                kekka = 3 # 被ツモ
            elif hora != tw and hojyu != tw:
                kekka = 4 # 横移動
        else:
            if any([i == tw for i in horaArray]):
                kekka = 1 # ロン
            elif all([i == tw for i in hojyuArray]):
                kekka = 2 # 放銃
            else:
                kekka = 4 # 横移動
    # 流局の場合
    elif 'RYUUKYOKU' in init:
        if not 'type' in init:
            if init.count('hai' + str(tw)) == 2:
                kekka = 5 # テンパイ
            else:
                kekka = 6 # ノーテン
        else:
            totyu = re.search(r'type=\"[a-z0-9]+\"', init).group()[6:-1]
            if totyu == 'yao9':
                kekka = 7 # 九種九牌
            if totyu == 'reach4':
                kekka = 8 # 四家立直
            if totyu == 'ron3':
                kekka = 9 # 三家和了
            if totyu == 'kan4':
                kekka = 10 # 四槓散了
            if totyu == 'kaze4':
                kekka = 11 # 四風連打
            if totyu == 'nm':
                kekka = 12 # 流し満貫
    return kekka

# 局の状態を判定
def judgeJyotai(init, tw):
    reachHassei = 0 # リーチ発声
    resHassei = re.search(r'REACH who=\"' + str(tw) + r'\" step=\"1\"', init)
    reachSeiritsu = 0 # リーチ成立
    resSeiritsu = re.search(r'REACH who=\"' + str(tw) + r'\" ten=\"[0-9,-]+\" step=\"2\"', init)
    furiten = None # フリテンリーチ
    if resHassei:
        reachHassei = 1
    if resSeiritsu:
        reachSeiritsu = 1
    array = re.findall(r'N who=\"' + str(tw) + r'\" m=\"[0-9]+\"', init)
    array = [int(i[13:-1]) for i in array]
    chi = 0 # チー
    pon = 0 # ポン
    kakan = 0 # 加カン
    nuki = 0 # 北抜き
    ankan = 0 # 暗カン
    daiminkan = 0 # ダイミンカン
    for i in range(len(array)):
        naki = judgeNaki(array[i])
        if naki == 0:
            chi += 1
        elif naki == 1:
            pon += 1
        elif naki == 2:
            kakan += 1
        elif naki == 3:
            nuki += 1
        elif naki == 4:
            ankan += 1
        elif naki == 5:
            daiminkan += 1
    furo = chi + pon + daiminkan # フーロ
    kan = kakan + daiminkan + ankan # カン
    jyunSengen = None # リーチ・フーロ巡目
    if reachHassei == 1 or furo >= 1:
        jyunSengen = calcSengen(init, tw)
    machiReach = None # 待ちの形 (1=好形, 0=愚形)
    jyotai = [reachHassei, reachSeiritsu, furiten, furo, kan, jyunSengen, machiReach]
    return jyotai

# 得点収支を計算
def calcSyushi(init, tw, jyotai):
    array = re.findall(r'sc=\"[0-9,-]+\"', init)
    array = [int(i[4:-1].split(',')[tw * 2 + 1]) * 100 for i in array]
    syushi = 0
    for i in range(len(array)):
        syushi += array[i]
    # リーチの場合
    if jyotai[1] == 1:
        syushi -= 1000
    return syushi

# 和了・放銃打点を計算
def calcTen(init, tw, kekka, horaArray, hojyuArray):
    daten = None # 素点
    cat = None # カテゴリー(0=満貫未満, 1=満貫, 2=跳満, 3=倍満, 4=三倍満, 5=役満)
    jyunAgari = None # 和了・放銃巡目
    if kekka == 0 or kekka == 1 or kekka ==2:
        array = re.findall(r'ten=\"[0-9,]+\" yaku[man]*=\"[0-9,]+\"', init)
        tenArray = []
        daten = 0
        for i in range(len(array)):
            tenTmp = re.search(r'ten=\"[0-9,]+\"', array[i]).group()[5:-1].split(',')
            tenTmp = [int(j) for j in tenTmp]
            tenArray.append(tenTmp)
        for i in range(len(array)):
            if horaArray[i] == tw or hojyuArray[i] == tw:
                daten += tenArray[i][1]
                if cat == None or cat <= tenArray[i][2]:
                    cat = tenArray[i][2]
                if (cat == None or cat == 0) and (tenArray[i][1] == 7700 or tenArray[i][1] == 7900 or tenArray[i][1] == 11600 or tenArray[i][1] == 11700):
                    cat = 1
        jyunAgari = calcAgari(init, tw)
    machiHora = None # 待ちの形 (1=好形, 0=愚形)
    shantenHojyu = None # 放銃時シャンテン数
    hojyuOya = None # 親に放銃 (1=親, 0=子)
    if kekka == 2:
        for i in range(len(hojyuArray)):
            if judgeOya(init, hojyuArray[i]) == 1:
                hojyuOya = 1
    ten = [daten, cat, jyunAgari, machiHora, shantenHojyu, hojyuOya]
    return ten

# 和了・放銃役を計算
def calcYaku(init, tw, kekka, horaArray, hojyuArray):
    yaku = [0] * 55
    if kekka == 0 or kekka == 1 or kekka ==2:
        array = re.findall(r'ten=\"[0-9,]+\" yaku[man]*=\"[0-9,]+\"', init)
        yakuArray = []
        for i in range(len(array)):
            # 役満の場合
            if 'yakuman' in array[i]:
                yakumanTmp = re.search(r'yakuman=\"[0-9,]+\"', array[i]).group()[9:-1].split(',')
                yakumanTmp = [int(j) for j in yakumanTmp]
                tmp = []
                for k in range(len(yakumanTmp)):
                    tmp.append(yakumanTmp[k])
                    tmp.append(1)
                yakuArray.append(tmp)
            else:
                yakuTmp = re.search(r'yaku=\"[0-9,]+\"', array[i]).group()[6:-1].split(',')
                yakuTmp = [int(j) for j in yakuTmp]
                yakuArray.append(yakuTmp)
        for i in range(len(array)):
            if horaArray[i] == tw or hojyuArray[i] == tw:
                for j in range(len(yakuArray[i]) // 2):
                    # 役は翻数でなく出現回数をカウント
                    if yakuArray[i][j * 2] < 52:
                        yaku[yakuArray[i][j * 2]] += 1
                    # ドラは翻数=枚数をカウント
                    else:
                        yaku[yakuArray[i][j * 2]] += yakuArray[i][j * 2 + 1]
    return yaku

# 局データを取得
def getRound(init, tw):
    kyoku = int(re.search(r'seed=\"[0-9,]+\"', init).group()[6:-1].split(',')[4]) # 局 (0～3=東場, 4～7=南場, 8～11=西場)
    oya = judgeOya(init, tw) # 親 (親=1, 子=0)
    double = judgeDouble(init)
    horaArray = judgeHora(init)
    hojyuArray = judgeHojyu(init)
    kekka = judgeKekka(init, tw, double, horaArray, hojyuArray) # 局の結果 (0=ツモ, 1=ロン, 2=放銃, 3=被ツモ, 4=横移動, 5=テンパイ, 6=ノーテン, 7=九種九牌, 8=四家立直, 9=三家和了, 10=四槓散了, 11=四風連打, 12=流し満貫)
    jyotai = judgeJyotai(init, tw) # 局の状態
    syushi = calcSyushi(init, tw, jyotai) # 得点収支
    ten = calcTen(init, tw, kekka, horaArray, hojyuArray) # 和了・放銃打点
    yaku = calcYaku(init, tw, kekka, horaArray, hojyuArray) # 和了・放銃役
    round = [kyoku, oya, double, kekka] + jyotai + [syushi] + ten + yaku
    return round

# 分析
def analyze(df, lobbyIn, playernumIn, playerlevelIn, playlengthIn, kuitanariIn, akaariIn, sokutakuIn):
    # 変数
    # 総合
    gameCount = 0
    danGenzai = 0
    danSum = 0
    danMax = 0
    rateGenzai = 0
    rateSum = 0
    rateMax = 0
    rateTakuSum = 0
    ukiSum = 0
    scoreSum = 0
    firstCount = 0
    secondCount = 0
    thirdCount = 0
    fourthCount = 0
    tobiCount = 0
    # 局
    roundCount = 0
    roundCountOya = 0
    roundCountKo = 0
    syushiSum = 0
    syushiSumOya = 0
    syushiSumKo = 0
    horaCount = 0
    horaCountOya = 0
    horaCountKo = 0
    horaSotenSum = 0
    horaSotenSumOya = 0
    horaSotenSumKo = 0
    horaSyushiSum = 0
    horaJyunSum = 0
    horaDamaCount = 0
    horaDamaCountOya = 0
    horaDamaCountKo = 0
    horaDamaSotenSum = 0
    horaDamaSotenSumOya = 0
    horaDamaSotenSumKo = 0
    tsumoCount = 0
    ronCount = 0
    hojyuCount = 0
    hojyuCountOya = 0
    hojyuCountKo = 0
    hojyusuCount = 0
    hojyusuCountOya = 0
    hojyusuCountKo = 0
    hojyuSotenSum = 0
    hojyuSotenSumOya = 0
    hojyuSotenSumKo = 0
    hojyuSyushiSum = 0
    hojyuJyunSum = 0
    hojyuOyaCount = 0
    hojyuOyaSotenSum = 0
    reachCount = 0
    reachCountOya = 0
    reachCountKo = 0
    reachSyushiSum = 0
    reachSyushiSumOya = 0
    reachSyushiSumKo = 0
    reachJyunSum = 0
    reachHoraCount = 0
    reachHoraCountOya = 0
    reachHoraCountKo = 0
    reachHoraSotenSum = 0
    reachHoraSotenSumOya = 0
    reachHoraSotenSumKo = 0
    reachHoraJyunSum = 0
    reachTsumoCount = 0
    reachRonCount = 0
    reachHojyuCount = 0
    reachRyukyokuCount = 0
    furoCount = 0
    furoCountOya = 0
    furoCountKo = 0
    furoOneCount = 0
    furoTwoCount = 0
    furoThreeCount = 0
    furoFourCount = 0
    furoSyushiSum = 0
    furoSyushiSumOya = 0
    furoSyushiSumKo = 0
    furoJyunSum = 0
    furoHoraCount = 0
    furoHoraCountOya = 0
    furoHoraCountKo = 0
    furoHoraSotenSum = 0
    furoHoraSotenSumOya = 0
    furoHoraSotenSumKo = 0
    furoHoraJyunSum = 0
    furoTsumoCount = 0
    furoRonCount = 0
    furoHojyuCount = 0
    kanCount = 0
    kanSyushiSum = 0
    kanReachCount = 0
    kanHoraCount = 0
    kanHoraSotenSum = 0
    ryukyokuCount = 0
    ryukyokuTsujyoCount = 0
    ryukyokuTochuCount = 0
    ryukyokuSyushiSum = 0
    tenpaiCount = 0
    notenCount = 0
    tenpairyoSyushiSum = 0
    # カテゴリー
    horaManganLessCount = 0
    horaManganLessCountOya = 0
    horaManganLessCountKo = 0
    horaManganCount = 0
    horaHanemanCount = 0
    horaBaimanCount = 0
    horaSanbaimanCount = 0
    horaYakumanCount = 0
    hojyuManganLessCount = 0
    hojyuManganLessCountOya = 0
    hojyuManganLessCountKo = 0
    hojyuManganCount = 0
    hojyuHanemanCount = 0
    hojyuBaimanCount = 0
    hojyuSanbaimanCount = 0
    hojyuYakumanCount = 0
    reachHoraManganLessCount = 0
    reachHoraManganLessCountOya = 0
    reachHoraManganLessCountKo = 0
    furoHoraManganLessCount = 0
    furoHoraManganLessCountOya = 0
    furoHoraManganLessCountKo = 0
    # 役
    horaRiichiCount = 0
    horaIppatsuCount = 0
    horaPinfuCount = 0
    horaTanyaoCount = 0
    horaFanpaiCount = 0
    horaChiitoiCount = 0
    horaToitoiCount = 0
    horaSomeCount = 0
    horaDoraCount = 0
    hojyuRiichiCount = 0
    hojyuIppatsuCount = 0
    hojyuPinfuCount = 0
    hojyuTanyaoCount = 0
    hojyuFanpaiCount = 0
    hojyuChiitoiCount = 0
    hojyuToitoiCount = 0
    hojyuSomeCount = 0
    hojyuDoraCount = 0
    reachHoraIppatsuCount = 0
    reachHoraPinfuCount = 0
    reachHoraTanyaoCount = 0
    reachHoraUraCount = 0
    furoHoraTanyaoCount = 0
    furoHoraFanpaiCount = 0
    furoHoraToitoiCount = 0
    furoHoraSomeCount = 0
    furoHoraDoraCount = 0
    for i in range(len(df)):
        # 取得
        id = df[i][0][0]
        tw = df[i][0][1]
        lobby = df[i][0][2]
        playernum = df[i][0][3]
        playerlevel = df[i][0][4]
        playlength = df[i][0][5]
        kuitanari = df[i][0][6]
        akaari = df[i][0][7]
        sokutaku = df[i][0][8]
        dan = df[i][0][9]
        rate = df[i][0][10]
        rateTaku = df[i][0][11]
        soten = df[i][0][12]
        score = df[i][0][13]
        rank = df[i][0][14]
        uki = 0
        if lobby == lobbyIn and playernum == playernumIn and playerlevel == playerlevelIn and playlength == playlengthIn and kuitanari == kuitanariIn and akaari == akaariIn: # sokutaku == sokutakuIn
            # 集計
            gameCount += 1
            danSum += dan
            if danMax < dan:
                danMax = dan
            rateSum += rate
            if rateMax < rate:
                rateMax = rate
            if playernum == 4:
                uki = soten - 25000
            elif playernum == 3:
                uki = soten - 35000
            rateTakuSum += rateTaku
            ukiSum += uki
            scoreSum += score
            if rank == 1:
                firstCount += 1
            if rank == 2:
                secondCount += 1
            if rank == 3:
                thirdCount += 1
            if rank == 4:
                fourthCount += 1
            if soten < 0:
                tobiCount += 1
            for j in range(1, len(df[i])):
                # 取得
                kyoku = df[i][j][0]
                oya = df[i][j][1]
                double = df[i][j][2]
                kekka = df[i][j][3]
                reachHassei = df[i][j][4]
                reachSeiritsu = df[i][j][5]
                furiten = df[i][j][6]
                furo = df[i][j][7]
                kan = df[i][j][8]
                jyunSengen = df[i][j][9]
                machiReach = df[i][j][10]
                syushi = df[i][j][11]
                daten = df[i][j][12]
                cat = df[i][j][13]
                jyunAgari = df[i][j][14]
                machiHora = df[i][j][15]
                shantenHojyu = df[i][j][16]
                hojyuOya = df[i][j][17]
                # 役
                menzentsumo = df[i][j][18]
                riichi = df[i][j][19]
                ippatsu = df[i][j][20]
                chankan = df[i][j][21]
                rinsyan = df[i][j][22]
                haitei = df[i][j][23]
                hotei = df[i][j][24]
                pinfu = df[i][j][25]
                tanyao = df[i][j][26]
                iipeko = df[i][j][27]
                ziTon = df[i][j][28]
                ziNan = df[i][j][29]
                ziSya = df[i][j][30]
                ziPe = df[i][j][31]
                baTon = df[i][j][32]
                baNan = df[i][j][33]
                baSya = df[i][j][34]
                baPe = df[i][j][35]
                yakuHaku = df[i][j][36]
                yakuHatsu = df[i][j][37]
                yakuChun = df[i][j][38]
                daburii = df[i][j][39]
                chiitoi = df[i][j][40]
                chanta = df[i][j][41]
                itsu = df[i][j][42]
                sansyoku = df[i][j][43]
                sandoko = df[i][j][44]
                sankan = df[i][j][45]
                toitoi = df[i][j][46]
                sanan = df[i][j][47]
                syosan = df[i][j][48]
                honro = df[i][j][49]
                ryanpeko = df[i][j][50]
                zyunchan = df[i][j][51]
                honitsu = df[i][j][52]
                chinitsu = df[i][j][53]
                renho = df[i][j][54]
                tenho = df[i][j][55]
                chiho = df[i][j][56]
                daisan = df[i][j][57]
                suan = df[i][j][58]
                suanTan = df[i][j][59]
                tsuiso = df[i][j][60]
                ryuiso = df[i][j][61]
                chinro = df[i][j][62]
                churen = df[i][j][63]
                churenJyun = df[i][j][64]
                kokushi = df[i][j][65]
                kokushiJyusan = df[i][j][66]
                daisu = df[i][j][67]
                syosu = df[i][j][68]
                sukan = df[i][j][69]
                doraOmo = df[i][j][70]
                doraUra = df[i][j][71]
                doraAka = df[i][j][72]
                # 集計
                roundCount += 1
                syushiSum += syushi
                if kekka == 0 or kekka == 1:
                    horaCount += 1
                    horaSotenSum += daten
                    horaSyushiSum += syushi
                    horaJyunSum += jyunAgari
                    if reachHassei == 0 and furo == 0:
                        horaDamaCount += 1
                        horaDamaSotenSum += daten
                    if cat == 0:
                        horaManganLessCount += 1
                    elif cat == 1:
                        horaManganCount += 1
                    elif cat == 2:
                        horaHanemanCount += 1
                    elif cat == 3:
                        horaBaimanCount += 1
                    elif cat == 4:
                        horaSanbaimanCount += 1
                    elif cat == 5:
                        horaYakumanCount += 1
                    horaRiichiCount += riichi
                    horaIppatsuCount += ippatsu
                    horaPinfuCount += pinfu
                    horaTanyaoCount += tanyao
                    horaFanpaiCount += ziTon
                    horaFanpaiCount += ziNan
                    horaFanpaiCount += ziSya
                    horaFanpaiCount += ziPe
                    horaFanpaiCount += baTon
                    horaFanpaiCount += baNan
                    horaFanpaiCount += baSya
                    horaFanpaiCount += baPe
                    horaFanpaiCount += yakuHaku
                    horaFanpaiCount += yakuHatsu
                    horaFanpaiCount += yakuChun
                    horaChiitoiCount += chiitoi
                    horaToitoiCount += toitoi
                    horaSomeCount += honitsu
                    horaSomeCount += chinitsu
                    horaDoraCount += doraOmo
                    horaDoraCount += doraUra
                    horaDoraCount += doraAka
                if kekka == 0:
                    tsumoCount += 1
                elif kekka == 1:
                    ronCount += 1
                elif kekka == 2:
                    hojyuCount += 1
                    hojyusuCount += 1
                    if double >= 1:
                        hojyusuCount += double
                    hojyuSotenSum += daten
                    hojyuSyushiSum += syushi
                    hojyuJyunSum += jyunAgari
                    if hojyuOya == 1:
                        hojyuOyaCount += 1
                        hojyuOyaSotenSum += daten
                    if cat == 0:
                        hojyuManganLessCount += 1
                    elif cat == 1:
                        hojyuManganCount += 1
                    elif cat == 2:
                        hojyuHanemanCount += 1
                    elif cat == 3:
                        hojyuBaimanCount += 1
                    elif cat == 4:
                        hojyuSanbaimanCount += 1
                    elif cat == 5:
                        hojyuYakumanCount += 1
                    hojyuRiichiCount += riichi
                    hojyuIppatsuCount += ippatsu
                    hojyuPinfuCount += pinfu
                    hojyuTanyaoCount += tanyao
                    hojyuFanpaiCount += ziTon
                    hojyuFanpaiCount += ziNan
                    hojyuFanpaiCount += ziSya
                    hojyuFanpaiCount += ziPe
                    hojyuFanpaiCount += baTon
                    hojyuFanpaiCount += baNan
                    hojyuFanpaiCount += baSya
                    hojyuFanpaiCount += baPe
                    hojyuFanpaiCount += yakuHaku
                    hojyuFanpaiCount += yakuHatsu
                    hojyuFanpaiCount += yakuChun
                    hojyuChiitoiCount += chiitoi
                    hojyuToitoiCount += toitoi
                    hojyuSomeCount += honitsu
                    hojyuSomeCount += chinitsu
                    hojyuDoraCount += doraOmo
                    hojyuDoraCount += doraUra
                    hojyuDoraCount += doraAka
                if reachHassei == 1:
                    reachCount += 1
                    reachSyushiSum += syushi
                    reachJyunSum += jyunSengen
                    if kekka == 0 or kekka == 1:
                        reachHoraCount += 1
                        reachHoraSotenSum += daten
                        reachHoraJyunSum += jyunAgari
                        if cat == 0:
                            reachHoraManganLessCount += 1
                        reachHoraIppatsuCount += ippatsu
                        reachHoraPinfuCount += pinfu
                        reachHoraTanyaoCount += tanyao
                        reachHoraUraCount += doraUra
                    if kekka == 0:
                        reachTsumoCount += 1
                    elif kekka == 1:
                        reachRonCount += 1
                    elif kekka == 2:
                        reachHojyuCount += 1
                    elif kekka == 5:
                        reachRyukyokuCount += 1
                if furo >= 1:
                    furoCount += 1
                    furoSyushiSum += syushi
                    furoJyunSum += jyunSengen
                    if furo == 1:
                        furoOneCount += 1
                    elif furo == 2:
                        furoTwoCount += 1
                    elif furo == 3:
                        furoThreeCount += 1
                    elif furo == 4:
                        furoFourCount += 1
                    if kekka == 0 or kekka == 1:
                        furoHoraCount += 1
                        furoHoraSotenSum += daten
                        furoHoraJyunSum += jyunAgari
                        if cat == 0:
                            furoHoraManganLessCount += 1
                        furoHoraTanyaoCount += tanyao
                        furoHoraFanpaiCount += ziTon
                        furoHoraFanpaiCount += ziNan
                        furoHoraFanpaiCount += ziSya
                        furoHoraFanpaiCount += ziPe
                        furoHoraFanpaiCount += baTon
                        furoHoraFanpaiCount += baNan
                        furoHoraFanpaiCount += baSya
                        furoHoraFanpaiCount += baPe
                        furoHoraFanpaiCount += yakuHaku
                        furoHoraFanpaiCount += yakuHatsu
                        furoHoraFanpaiCount += yakuChun
                        furoHoraToitoiCount += toitoi
                        furoHoraSomeCount += honitsu
                        furoHoraSomeCount += chinitsu
                        furoHoraDoraCount += doraOmo
                        furoHoraDoraCount += doraAka
                    if kekka == 0:
                        furoTsumoCount += 1
                    elif kekka == 1:
                        furoRonCount += 1
                    elif kekka == 2:
                        furoHojyuCount += 1
                if kan >= 1:
                    kanCount += 1
                    kanSyushiSum += syushi
                    if reachHassei == 1:
                        kanReachCount += 1
                    if kekka == 0 or kekka == 1:
                        kanHoraCount += 1
                        kanHoraSotenSum += daten
                if kekka == 5 or kekka == 6 or kekka == 7 or kekka == 8 or kekka == 9 or kekka == 10 or kekka == 11 or kekka == 12:
                    ryukyokuCount += 1
                    ryukyokuSyushiSum += syushi
                    if kekka == 5 or kekka == 6:
                        ryukyokuTsujyoCount += 1
                        tenpairyoSyushiSum += syushi
                        if reachSeiritsu == 1:
                            tenpairyoSyushiSum += 1000
                        if kekka == 5:
                            tenpaiCount += 1
                        elif kekka == 6:
                            notenCount += 1
                    elif kekka == 7 or kekka == 8 or kekka == 9 or kekka == 10 or kekka == 11 or kekka == 12:
                        ryukyokuTochuCount += 1
                # 親
                if oya == 1:
                    roundCountOya += 1
                    syushiSumOya += syushi
                    if kekka == 0 or kekka == 1:
                        horaCountOya += 1
                        horaSotenSumOya += daten
                        if reachHassei == 0 and furo == 0:
                            horaDamaCountOya += 1
                            horaDamaSotenSumOya += daten
                        if cat == 0:
                            horaManganLessCountOya += 1
                    elif kekka == 2:
                        hojyuCountOya += 1
                        hojyusuCountOya += 1
                        if double >= 1:
                            hojyusuCountOya += double
                        hojyuSotenSumOya += daten
                        if cat == 0:
                            hojyuManganLessCountOya += 1
                    if reachHassei == 1:
                        reachCountOya += 1
                        reachSyushiSumOya += syushi
                        if kekka == 0 or kekka == 1:
                            reachHoraCountOya += 1
                            reachHoraSotenSumOya += daten
                            if cat == 0:
                                reachHoraManganLessCountOya += 1
                    if furo >= 1:
                        furoCountOya += 1
                        furoSyushiSumOya += syushi
                        if kekka == 0 or kekka == 1:
                            furoHoraCountOya += 1
                            furoHoraSotenSumOya += daten
                            if cat == 0:
                                furoHoraManganLessCountOya += 1
                # 子
                if oya == 0:
                    roundCountKo += 1
                    syushiSumKo += syushi
                    if kekka == 0 or kekka == 1:
                        horaCountKo += 1
                        horaSotenSumKo += daten
                        if reachHassei == 0 and furo == 0:
                            horaDamaCountKo += 1
                            horaDamaSotenSumKo += daten
                        if cat == 0:
                            horaManganLessCountKo += 1
                    elif kekka == 2:
                        hojyuCountKo += 1
                        hojyusuCountKo += 1
                        if double >= 1:
                            hojyusuCountKo += double
                        hojyuSotenSumKo += daten
                        if cat == 0:
                            hojyuManganLessCountKo += 1
                    if reachHassei == 1:
                        reachCountKo += 1
                        reachSyushiSumKo += syushi
                        if kekka == 0 or kekka == 1:
                            reachHoraCountKo += 1
                            reachHoraSotenSumKo += daten
                            if cat == 0:
                                reachHoraManganLessCountKo += 1
                    if furo >= 1:
                        furoCountKo += 1
                        furoSyushiSumKo += syushi
                        if kekka == 0 or kekka == 1:
                            furoHoraCountKo += 1
                            furoHoraSotenSumKo += daten
                            if cat == 0:
                                furoHoraManganLessCountKo += 1
    # 計算
    # 総合データ
    firstPer = float(format(firstCount / gameCount, '.3f'))
    secondPer = float(format(secondCount / gameCount, '.3f'))
    thirdPer = float(format(thirdCount / gameCount, '.3f'))
    fourthPer = float(format(fourthCount / gameCount, '.3f'))
    tobiPer = float(format(tobiCount / gameCount, '.3f'))
    rankAve = float(format((firstCount * 1 + secondCount * 2 + thirdCount * 3 + fourthCount * 4) / gameCount, '.3f'))
    ukiAve = float(format(ukiSum / gameCount, '.3f'))
    scoreAve = float(format(scoreSum / gameCount, '.3f'))
    danGenzai = df[len(df) - 1][0][9]
    danAve = float(format(danSum / gameCount, '.3f'))
    danAntei = float(format(7 + ((firstCount * 90 + secondCount * 45) / fourthCount - 135) / 15, '.3f'))
    if danGenzai >= 9:
        danGenzai = danGenzai - 9
    else:
        danGenzai = 0
    if danMax >= 9:
        danMax = danMax - 9
    else:
        danMax = 0
    if danAve >= 9:
        danAve = float(format(danAve - 9, '.3f'))
    else:
        danAve = 0
    rateGenzai = df[len(df) - 1][0][10]
    rateAve = float(format(rateSum / gameCount, '.3f'))
    rateAntei = float(format(rateTakuSum / gameCount + (50 - rankAve * 20) * 160 / 3, '.3f'))
    syushiAve = float(format(syushiSum / roundCount, '.3f'))
    syushiAveOya = float(format(syushiSumOya / roundCountOya, '.3f'))
    syushiAveKo = float(format(syushiSumKo / roundCountKo, '.3f'))
    gameData = [gameCount, firstCount, secondCount, thirdCount, fourthCount, tobiCount, firstPer, secondPer, thirdPer, fourthPer, tobiPer,
        rankAve, ukiSum, ukiAve, scoreSum, scoreAve, roundCount, syushiAve, syushiAveOya, syushiAveKo,
        danGenzai, danMax, danAve, danAntei, rateGenzai, rateMax, rateAve, rateAntei]
    # 和了データ
    horaPer = float(format(horaCount / roundCount, '.3f'))
    horaSotenAve = float(format(horaSotenSum / horaCount, '.3f'))
    horaSyushiAve = float(format(horaSyushiSum / horaCount, '.3f'))
    horaJyunAve = float(format(horaJyunSum / horaCount, '.3f'))
    horaManganLessPer = float(format(horaManganLessCount / horaCount, '.3f'))
    horaManganPer = float(format(horaManganCount / horaCount, '.3f'))
    horaHanemanPer = float(format(horaHanemanCount / horaCount, '.3f'))
    horaBaimanPer = float(format(horaBaimanCount / horaCount, '.3f'))
    horaSanbaimanPer = float(format(horaSanbaimanCount / horaCount, '.3f'))
    horaYakumanPer = float(format(horaYakumanCount / horaCount, '.3f'))
    horaManganMorePer = float(format((horaCount - horaManganLessCount) / horaCount, '.3f'))
    horaRiichiPer = float(format(horaRiichiCount / horaCount, '.3f'))
    horaPinfuPer = float(format(horaPinfuCount / horaCount, '.3f'))
    horaTanyaoPer = float(format(horaTanyaoCount / horaCount, '.3f'))
    horaFanpaiPer = float(format(horaFanpaiCount / horaCount, '.3f'))
    horaChiitoiPer = float(format(horaChiitoiCount / horaCount, '.3f'))
    horaToitoiPer = float(format(horaToitoiCount / horaCount, '.3f'))
    horaSomePer = float(format(horaSomeCount / horaCount, '.3f'))
    horaIppatsuPer = float(format(horaIppatsuCount / horaCount, '.3f'))
    horaDoraAve = float(format(horaDoraCount / horaCount, '.3f'))
    horaTsumoPer = float(format(tsumoCount / horaCount, '.3f'))
    horaDamaPer = float(format(horaDamaCount / horaCount, '.3f'))
    horaDamaSotenAve = float(format(horaDamaSotenSum / horaDamaCount, '.3f'))
    horaPerOya = float(format(horaCountOya / roundCountOya, '.3f'))
    horaSotenAveOya = float(format(horaSotenSumOya / horaCountOya, '.3f'))
    horaManganMorePerOya = float(format((horaCountOya - horaManganLessCountOya) / horaCountOya, '.3f'))
    horaDamaPerOya = float(format(horaDamaCountOya / horaCountOya, '.3f'))
    horaDamaSotenAveOya = float(format(horaDamaSotenSumOya / horaDamaCountOya, '.3f'))
    horaPerKo = float(format(horaCountKo / roundCountKo, '.3f'))
    horaSotenAveKo = float(format(horaSotenSumKo / horaCountKo, '.3f'))
    horaManganMorePerKo = float(format((horaCountKo - horaManganLessCountKo) / horaCountKo, '.3f'))
    horaDamaPerKo = float(format(horaDamaCountKo / horaCountKo, '.3f'))
    horaDamaSotenAveKo = float(format(horaDamaSotenSumKo / horaDamaCountKo, '.3f'))
    horaData = [horaPer, horaSotenAve, horaSyushiAve, horaJyunAve, horaManganLessPer, horaManganPer, horaHanemanPer, horaBaimanPer, horaSanbaimanPer, horaYakumanPer, horaManganMorePer,
        horaRiichiPer, horaPinfuPer, horaTanyaoPer, horaFanpaiPer, horaChiitoiPer, horaToitoiPer, horaSomePer, horaIppatsuPer, horaDoraAve,
        horaTsumoPer, horaDamaPer, horaDamaSotenAve,
        horaPerOya, horaSotenAveOya, horaManganMorePerOya, horaDamaPerOya, horaDamaSotenAveOya, horaPerKo, horaSotenAveKo, horaManganMorePerKo, horaDamaPerKo, horaDamaSotenAveKo]
    # 放銃データ
    hojyuPer = float(format(hojyuCount / roundCount, '.3f'))
    hojyuSotenAve = float(format(hojyuSotenSum / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuSyushiAve = float(format(hojyuSyushiSum / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuJyunAve = float(format(hojyuJyunSum / hojyuCount, '.3f'))
    hojyuManganLessPer = float(format(hojyuManganLessCount / hojyuCount, '.3f')) # 厳密でない
    hojyuManganPer = float(format(hojyuManganCount / hojyuCount, '.3f')) # 厳密でない
    hojyuHanemanPer = float(format(hojyuHanemanCount / hojyuCount, '.3f')) # 厳密でない
    hojyuBaimanPer = float(format(hojyuBaimanCount / hojyuCount, '.3f')) # 厳密でない
    hojyuSanbaimanPer = float(format(hojyuSanbaimanCount / hojyuCount, '.3f')) # 厳密でない
    hojyuYakumanPer = float(format(hojyuYakumanCount / hojyuCount, '.3f')) # 厳密でない
    hojyuManganMorePer = float(format((hojyuCount - hojyuManganLessCount) / hojyuCount, '.3f')) # 厳密でない
    hojyuRiichiPer = float(format(hojyuRiichiCount / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuPinfuPer = float(format(hojyuPinfuCount / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuTanyaoPer = float(format(hojyuTanyaoCount / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuFanpaiPer = float(format(hojyuFanpaiCount / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuChiitoiPer = float(format(hojyuChiitoiCount / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuToitoiPer = float(format(hojyuToitoiCount / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuSomePer = float(format(hojyuSomeCount / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuIppatsuPer = float(format(hojyuIppatsuCount / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuDoraAve = float(format(hojyuDoraCount / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuOyaPer = float(format(hojyuOyaCount / hojyusuCount, '.3f')) # 放銃回数で割る
    hojyuOyaSotenAve = float(format(hojyuOyaSotenSum / hojyuOyaCount, '.3f')) # 厳密でない
    hojyuPerOya = float(format(hojyuCountOya / roundCountOya, '.3f'))
    hojyuSotenAveOya = float(format(hojyuSotenSumOya / hojyusuCountOya, '.3f'))
    hojyuManganMorePerOya = float(format((hojyuCountOya - hojyuManganLessCountOya) / hojyuCountOya, '.3f'))
    hojyuPerKo = float(format(hojyuCountKo / roundCountKo, '.3f'))
    hojyuSotenAveKo = float(format(hojyuSotenSumKo / hojyusuCountKo, '.3f'))
    hojyuManganMorePerKo = float(format((hojyuCountKo - hojyuManganLessCountKo) / hojyuCountKo, '.3f'))
    hojyuData = [hojyuPer, hojyuSotenAve, hojyuSyushiAve, hojyuJyunAve, hojyuManganLessPer, hojyuManganPer, hojyuHanemanPer, hojyuBaimanPer, hojyuSanbaimanPer, hojyuYakumanPer, hojyuManganMorePer,
        hojyuRiichiPer, hojyuPinfuPer, hojyuTanyaoPer, hojyuFanpaiPer, hojyuChiitoiPer, hojyuToitoiPer, hojyuSomePer, hojyuIppatsuPer, hojyuDoraAve,
        hojyuOyaPer, hojyuOyaSotenAve, hojyuPerOya, hojyuSotenAveOya, hojyuManganMorePerOya, hojyuPerKo, hojyuSotenAveKo, hojyuManganMorePerKo]
    # 立直データ
    reachPer = float(format(reachCount / roundCount, '.3f'))
    reachSyushiAve = float(format(reachSyushiSum / reachCount, '.3f'))
    reachJyunAve = float(format(reachJyunSum / reachCount, '.3f'))
    reachHoraPer = float(format(reachHoraCount / reachCount, '.3f'))
    reachHojyuPer = float(format(reachHojyuCount / reachCount, '.3f'))
    reachRyukyokuPer = float(format(reachRyukyokuCount / reachCount, '.3f'))
    reachHoraSotenAve = float(format(reachHoraSotenSum / reachHoraCount, '.3f'))
    reachHoraJyunAve = float(format(reachHoraJyunSum / reachHoraCount, '.3f'))
    reachHoraManganMorePer = float(format((reachHoraCount - reachHoraManganLessCount) / reachHoraCount, '.3f'))
    reachHoraPinfuPer = float(format(reachHoraPinfuCount / reachHoraCount, '.3f'))
    reachHoraTanyaoPer = float(format(reachHoraTanyaoCount / reachHoraCount, '.3f'))
    reachHoraIppatsuPer = float(format(reachHoraIppatsuCount / reachHoraCount, '.3f'))
    reachHoraUraAve = float(format(reachHoraUraCount / reachHoraCount, '.3f'))
    reachHoraTsumoPer = float(format(reachTsumoCount / reachHoraCount, '.3f'))
    reachPerOya = float(format(reachCountOya / roundCountOya, '.3f'))
    reachSyushiAveOya = float(format(reachSyushiSumOya / reachCountOya, '.3f'))
    reachHoraPerOya = float(format(reachHoraCountOya / reachCountOya, '.3f'))
    reachHoraSotenAveOya = float(format(reachHoraSotenSumOya / reachHoraCountOya, '.3f'))
    reachHoraManganMorePerOya = float(format((reachHoraCountOya - reachHoraManganLessCountOya) / reachHoraCountOya, '.3f'))
    reachPerKo = float(format(reachCountKo / roundCountKo, '.3f'))
    reachSyushiAveKo = float(format(reachSyushiSumKo / reachCountKo, '.3f'))
    reachHoraPerKo = float(format(reachHoraCountKo / reachCountKo, '.3f'))
    reachHoraSotenAveKo = float(format(reachHoraSotenSumKo / reachHoraCountKo, '.3f'))
    reachHoraManganMorePerKo = float(format((reachHoraCountKo - reachHoraManganLessCountKo) / reachHoraCountKo, '.3f'))
    reachData = [reachPer, reachSyushiAve, reachJyunAve, reachHoraPer, reachHojyuPer, reachRyukyokuPer, reachHoraSotenAve, reachHoraJyunAve,
        reachHoraManganMorePer, reachHoraPinfuPer, reachHoraTanyaoPer, reachHoraIppatsuPer, reachHoraUraAve, reachHoraTsumoPer,
        reachPerOya, reachSyushiAveOya, reachHoraPerOya, reachHoraSotenAveOya, reachHoraManganMorePerOya,
        reachPerKo, reachSyushiAveKo, reachHoraPerKo, reachHoraSotenAveKo, reachHoraManganMorePerKo]
    # 副露データ
    furoPer = float(format(furoCount / roundCount, '.3f'))
    furoOnePer = float(format(furoOneCount / roundCount, '.3f'))
    furoTwoPer = float(format(furoTwoCount / roundCount, '.3f'))
    furoThreePer = float(format(furoThreeCount / roundCount, '.3f'))
    furoFourPer = float(format(furoFourCount / roundCount, '.3f'))
    furoSyushiAve = float(format(furoSyushiSum / furoCount, '.3f'))
    furoJyunAve = float(format(furoJyunSum / furoCount, '.3f'))
    furoHoraPer = float(format(furoHoraCount / furoCount, '.3f'))
    furoHojyuPer = float(format(furoHojyuCount / furoCount, '.3f'))
    furoHoraSotenAve = float(format(furoHoraSotenSum / furoHoraCount, '.3f'))
    furoHoraJyunAve = float(format(furoHoraJyunSum / furoHoraCount, '.3f'))
    furoHoraManganMorePer = float(format((furoHoraCount - furoHoraManganLessCount) / furoHoraCount, '.3f'))
    furoHoraTanyaoPer = float(format(furoHoraTanyaoCount / furoHoraCount, '.3f'))
    furoHoraFanpaiPer = float(format(furoHoraFanpaiCount / furoHoraCount, '.3f'))
    furoHoraToitoiPer = float(format(furoHoraToitoiCount / furoHoraCount, '.3f'))
    furoHoraSomePer = float(format(furoHoraSomeCount / furoHoraCount, '.3f'))
    furoHoraDoraAve = float(format(furoHoraDoraCount / furoHoraCount, '.3f'))
    furoHoraTsumoPer = float(format(furoTsumoCount / furoHoraCount, '.3f'))
    furoPerOya = float(format(furoCountOya / roundCountOya, '.3f'))
    furoSyushiAveOya = float(format(furoSyushiSumOya / furoCountOya, '.3f'))
    furoHoraPerOya = float(format(furoHoraCountOya / furoCountOya, '.3f'))
    furoHoraSotenAveOya = float(format(furoHoraSotenSumOya / furoHoraCountOya, '.3f'))
    furoHoraManganMorePerOya = float(format((furoHoraCountOya - furoHoraManganLessCountOya) / furoHoraCountOya, '.3f'))
    furoPerKo = float(format(furoCountKo / roundCountKo, '.3f'))
    furoSyushiAveKo = float(format(furoSyushiSumKo / furoCountKo, '.3f'))
    furoHoraPerKo = float(format(furoHoraCountKo / furoCountKo, '.3f'))
    furoHoraSotenAveKo = float(format(furoHoraSotenSumKo / furoHoraCountKo, '.3f'))
    furoHoraManganMorePerKo = float(format((furoHoraCountKo - furoHoraManganLessCountKo) / furoHoraCountKo, '.3f'))
    furoData = [furoPer, furoOnePer, furoTwoPer, furoThreePer, furoFourPer, furoSyushiAve, furoJyunAve, furoHoraPer, furoHojyuPer, furoHoraSotenAve, furoHoraJyunAve,
        furoHoraManganMorePer, furoHoraTanyaoPer, furoHoraFanpaiPer, furoHoraToitoiPer, furoHoraSomePer, furoHoraDoraAve, furoHoraTsumoPer,
        furoPerOya, furoSyushiAveOya, furoHoraPerOya, furoHoraSotenAveOya, furoHoraManganMorePerOya,
        furoPerKo, furoSyushiAveKo, furoHoraPerKo, furoHoraSotenAveKo, furoHoraManganMorePerKo]
    # カンデータ
    kanPer = float(format(kanCount / roundCount, '.3f'))
    kanSyushiAve = float(format(kanSyushiSum / kanCount, '.3f'))
    kanReachPer = float(format(kanReachCount / kanCount, '.3f'))
    kanHoraPer = float(format(kanHoraCount / kanCount, '.3f'))
    kanHoraSotenAve = float(format(kanHoraSotenSum / kanHoraCount, '.3f'))
    kanData = [kanPer, kanSyushiAve, kanReachPer, kanHoraPer, kanHoraSotenAve]
    # 流局データ
    ryukyokuPer = float(format(ryukyokuCount / roundCount, '.3f'))
    ryukyokuTsujyoPer = float(format(ryukyokuTsujyoCount / roundCount, '.3f'))
    ryukyokuTochuPer = float(format(ryukyokuTochuCount / roundCount, '.3f'))
    ryukyokuSyushiAve = float(format(ryukyokuSyushiSum / ryukyokuCount, '.3f'))
    tenpaiPer = float(format(tenpaiCount / ryukyokuTsujyoCount, '.3f'))
    tenpairyoSyushiAve = float(format(tenpairyoSyushiSum / ryukyokuTsujyoCount, '.3f'))
    ryukyokuData = [ryukyokuPer, ryukyokuTsujyoPer, ryukyokuTochuPer, ryukyokuSyushiAve, tenpaiPer, tenpairyoSyushiAve]
    # 結合
    analysis = gameData + horaData + hojyuData + reachData + furoData + kanData + ryukyokuData
    return analysis

# 実行
folders = glob.glob('Tenhou/Research/log/鳳凰卓/**/')
analyses = []
header = ['名前', '試合数', '１位', '２位', '３位', '４位', '飛び', '１位率', '２位率', '３位率', '４位率', '飛び率',
    '平均順位', '通算収支', '平均収支', '通算スコア', '平均スコア', '局数', '局収支', '親局収支', '子局収支',
    '段位', '最高段位', '平均段位', '安定段位', 'レート', '最高レート', '平均レート', '安定レート',
    '和了率', '和了素点', '和了収入', '和了巡目', '和了満貫未満', '和了満貫', '和了跳満', '和了倍満', '和了三倍満', '和了役満', '和了満貫以上',
    '和了リーチ', '和了ピンフ', '和了タンヤオ', '和了ファンパイ', '和了チートイ', '和了トイトイ', '和了染め手', '和了一発', '和了ドラ枚数',
    'ツモアガり割合', 'ダマテン割合', 'ダマテン素点',
    '親和了率', '親和了素点', '親和了満貫以上', '親ダマテン割合', '親ダマテン素点', '子和了率', '子和了素点', '子和了満貫以上', '子ダマテン割合', '子ダマテン素点',
    '放銃率', '放銃素点', '放銃支出', '放銃巡目', '放銃満貫未満', '放銃満貫', '放銃跳満', '放銃倍満', '放銃三倍満', '放銃役満', '放銃満貫以上',
    '放銃リーチ', '放銃ピンフ', '放銃タンヤオ', '放銃ファンパイ', '放銃チートイ', '放銃トイトイ', '放銃染め手', '放銃一発', '放銃ドラ枚数',
    '親に放銃割合', '親に放銃素点', '親放銃率', '親放銃素点', '親放銃満貫以上', '子放銃率', '子放銃素点', '子放銃満貫以上',
    '立直率', '立直収支', '立直巡目', '立直和了率', '立直放銃率', '立直流局率', '立直和了素点', '立直和了巡目',
    '立直和了満貫以上', '立直和了ピンフ', '立直和了タンヤオ', '立直和了一発', '立直和了裏ドラ枚数', '立直ツモアガり割合',
    '親立直率', '親立直収支', '親立直和了率', '親立直和了素点', '親立直和了満貫以上',
    '子立直率', '子立直収支', '子立直和了率', '子立直和了素点', '子立直和了満貫以上',
    '副露率', '１副露率', '２副露率', '３副露率', '４副露率', '副露収支', '副露巡目', '副露和了率', '副露放銃率', '副露和了素点', '副露和了巡目',
    '副露和了満貫以上', '副露和了タンヤオ', '副露和了ファンパイ', '副露和了トイトイ', '副露和了染め手', '副露和了ドラ枚数', '副露ツモアガり割合',
    '親副露率', '親副露収支', '親副露和了率', '親副露和了素点', '親副露和了満貫以上',
    '子副露率', '子副露収支', '子副露和了率', '子副露和了素点', '子副露和了満貫以上',
    'カン率', 'カン収支', 'カン立直率', 'カン和了率', 'カン和了素点',
    '流局率', '通常流局率', '途中流局率', '流局収支', 'テンパイ率', 'テンパイ収支']
analyses.append(header)
for folder in folders:
    name = os.path.basename(os.path.dirname(folder)) # プレーヤー名
    namePer = encodePer(name) # パーセントエンコードされたプレーヤー名
    files = glob.glob(folder + '*.mjlog')
    df = []
    for file in files:
        with gzip.open(file, mode='rt', encoding='utf-8') as f:
            xml = f.read()
        id = re.search(r'[a-z0-9-]+&tw=', os.path.splitext(os.path.basename(file))[0]).group()[:-4] # ゲームID
        tw = judgeTw(file, xml, namePer) # 席順
        try:
            game = getGame(xml, id, tw) # ゲームデータ
            init = xml.split('<INIT ')
            del init[0]
            rounds = []
            for i in range(len(init)):
                round = getRound(init[i], tw)
                rounds.append(round)
            data = [game] + rounds
            df.append(data)
        except:
            print('ERROR: ' + id)
            pass
    analysis = analyze(df, lobbyIn, playernumIn, playerlevelIn, playlengthIn, kuitanariIn, akaariIn, sokutakuIn)
    analyses.append([name] + analysis)
with open('Tenhou/Research/log/鳳凰卓/鳳凰卓.csv', 'w', newline='', encoding='utf_8') as g:
    writer = csv.writer(g, lineterminator='\n')
    writer.writerows(analyses)
print('done')
