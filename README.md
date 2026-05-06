# wine_wine

Mac 沒裝 pip 指令名稱很常見，用 python3 -m pip 即可：


python3 -m pip install requests pandas
如果出現 externally-managed-environment 錯誤（macOS 較新版 Python 會擋），有兩個選擇：

選項 1（推薦）：用 venv 虛擬環境


cd /Users/danniryu/Desktop/proj/wine_wine
python3 -m venv .venv
source .venv/bin/activate
pip install requests pandas
之後每次開新 terminal 要先 source .venv/bin/activate。