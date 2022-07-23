library(tidyverse)
library(corrplot)
library(MASS)
library(psych)
library(stargazer)
library(ggbiplot)

# 読み込み
hououtaku <- read.csv("./data/hououtaku_pre.csv", fileEncoding="UTF-8-BOM", header = T, row.names = 1)
tenhoui <- read.csv("./data/tenhoui_pre.csv", fileEncoding="UTF-8-BOM", header = T, row.names = 1)
league <- read.csv("./data/league_pre.csv", fileEncoding="UTF-8-BOM", header = T, row.names = 1)
# View(hououtaku)
# View(tenhoui)
# View(league)

# データフレームを作成
ln <- c(5, 8, 11, 13, 14, 16)
hououtaku_ln <- hououtaku
hououtaku_ln[,ln] <- log(hououtaku[,ln])
tenhoui_ln <- tenhoui
tenhoui_ln[,ln] <- log(tenhoui[,ln])
league_ln <- league
league_ln[,ln] <- log(league[,ln])
# View(hououtaku_ln)
# View(tenhoui_ln)
# View(league_ln)
df = rbind(tenhoui_ln, league_ln)
rownames(df) <- c("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "A", "B", "C", "D", "E", "F", "G", "H")
group <- c("天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "天鳳位", "リーグ戦", "リーグ戦", "リーグ戦", "リーグ戦", "リーグ戦", "リーグ戦", "リーグ戦", "リーグ戦")
df <- data.frame(df, group)
# View(df)

# 相関行列
corr <- round(cor(hououtaku_ln), 3)
col <- colorRampPalette(c("#BB4444", "#EE9988", "#FFFFFF", "#77AADD", "#4477AA"))
mx <- corrplot(corr, method = "shade", shade.col = NA, tl.col = "black", tl.srt = 45, col = col(200), addCoef.col = "black", cl.pos = "n")
pairs.panels(hououtaku_ln[1:4])
pairs.panels(hououtaku_ln[5:10])
pairs.panels(hououtaku_ln[11:16])

# 重回帰分析
# reg <- lm(安定レート ~ 和了率 + 和了素点 + 和了巡目 + 和了素点 : 和了巡目 + 放銃率 + 放銃素点 + 放銃巡目 + 放銃素点 : 放銃巡目 + 立直率 + 立直巡目 + 立直成功率 + 副露率 + 副露巡目 + 聴牌率, hououtaku_ln)
reg <- lm(安定レート ~ 和了率 + 和了素点 + 和了巡目 + 和了素点 : 和了巡目 + 放銃率 + 副露率, hououtaku_ln)
summary(reg)
regaic <- stepAIC(reg)
summary(regaic)
stargazer(reg)
pred <- predict(reg)
resid <- residuals(reg)
data.frame(hououtaku_ln[4], pred, resid)

# 主成分分析
pca <- prcomp(df[5:16], scale = T)
summary(pca)
biplot(pca)
round(pca$rotation, 3)
round(pca$x, 3)
cor(pca$x)
ggbiplot(pcobj = pca, choices = 1:2, obs.scale = 1, var.scale = 1, groups = df[,17], ellipse = T, circle = T, labels = rownames(df))
+ theme(legend.direction = "horizontal", legend.position = "top")
