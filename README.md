# Otoge Input Viewer
IIDXコントローラ(PHOENIX WANなど)の入力可視化、リリース速度や入力密度の表示が行えるソフトウェアです。
OBSへの設定をとても楽に行うことができます。  
らぐ様の[打鍵ディスプレイツール](https://rag-oji.com/dakendisplay/)の影響を多大に受けていますが、
IIDX以外のコントローラへの対応も考えており、立ち位置としては別物であるつもりです。

作者がPHOENIX WAN/FAUCE TWOしか持っていないため他のコントローラでの検証はできていません。

A tool for displaying inputs of IIDX-controller(eg. PHOENIX WAN, ...). It is easy to configure into OBS.
This tool is inspired from [dakendisplay tool](https://rag-oji.com/dakendisplay/).

<img src="https://github.com/user-attachments/assets/bdb98658-ca48-44f1-b605-40840372ef0b" width=500px>
<img src="https://github.com/user-attachments/assets/90ca18f6-c383-4c9c-98ec-b0709ff94226" width=500px>  

![image](https://github.com/user-attachments/assets/adb1d85c-b1b8-4215-85db-04f68acb8037)

# Usage (ツールの利用方法)
1. [Releaseページ](https://github.com/dj-kata/otoge_input_viewer/releases)の一番上にあるotoge_input_viewer.zipをダウンロードして解凍する。
2. otoge_input_viewer.exeを実行する。
3. 検出するコントローラを変更したい場合は```changeボタン```を押す
4. OBSにキー入力状況を表示したい場合は、同梱のHTMLファイル(htmlフォルダ内)をOBSにドラッグ&ドロップする。
5. SDVXで使いたい場合やリリース計算に使うノーツ数を変更したい場合は設定画面(```メニューバー内config```)から設定を変更してください。

メイン画面において、使いたいコントローラの名前が表示されていてかつ、modeが正しければOKです。
![image](https://github.com/user-attachments/assets/16f0f6e7-4dc8-4ec5-b488-41acead1b09d)


各ブラウザソースはデフォルトでは以下のように警告の文字が表示されていますが、
正しく接続されてなんらかの表示命令を受信した時点でこの文字が消えるようになっています。
(ツールの起動忘れを対策するために敢えて目立たせています)  
<img src="https://github.com/user-attachments/assets/27b4b07c-6d40-4563-98ec-afd8907c171e" width=500px>  

設定画面では、
- コントローラの種別(IIDX, SDVX)
- それ以上長い入力をロングノーツとみなすためのしきい値
- リリース速度計算のために直近何ノーツを用いるか
- 譜面密度計算のために直近何秒のノーツを見るか
- websocketで使うポート番号

を設定することができます。  
![image](https://github.com/user-attachments/assets/257ff66a-4ee7-4cf8-9353-ecf7600b29a8)  

同梱のHTMLファイルについては以下の通りとなっています。
|ファイル名|推奨サイズ|内容|
|-|-|-|
|html/iidx_1p.html|800×400|IIDX 1P側|
|html/iidx_2p.html|800×400|IIDX 2P側|
|html/sdvx.html|800×400|SDVX|
|html/stats_only.html|800×100|(リリース、密度、ノーツ数の数値のみ)|

WebSocketのポート番号はデフォルトの8765で問題ないつもりですが、
もし上手く動かない場合(他のアプリが掴んでいる等)は、他のポートに変更してみてください。
変更後はブラウザソースの再読み込みが必要です。(該当するブラウザソースをダブルクリックし、```現在のページのキャッシュを更新```をクリック)

また、本アプリの新バージョンがリリースされた際には、
アプリ起動時にアップデート機能が動くようになっています。


## デザインのカスタマイズ
### 背景画像を設定する
以下のように背景画像を設定することができます。  
<img src="https://github.com/user-attachments/assets/90ca18f6-c383-4c9c-98ec-b0709ff94226" width=500px>  

以下の手順で設定できます。
1. ```html```フォルダ内に背景画像を置く。(ここでは、ファイル名を```bg.png```とします。)
2. ディスプレイ表示用のブラウザソースをダブルクリックし、カスタムCSSに以下を追加してOKをクリック。

```css
.background{
    background-image: url("./bg.png");
}
```
ちなみに、背景画像を少し暗くしたい場合は以下にするとできます。
rgba(0,0,0,0.65)の4つ目が不透明度で、この値が大きいほど暗くなります。適宜調整してください。
```css
.background{
    background-image: linear-gradient(rgba(0,0,0,0.65),rgba(0,0,0,0.65)),url(bg.png);
}
```
![image](https://github.com/user-attachments/assets/96d26157-6f8f-4046-9c75-170737ac9876)

### 背景に色を付ける
(CSSの初歩みたいな内容ですが、一応書いておきます。)  
OBSでは、ブラウザソースにデフォルトで以下のようなカスタムCSSが設定されます。
```
body { background-color: rgba(0, 0, 0, 0); margin: 0px auto; overflow: hidden; }
```
背景色が透明にされてしまい、配信画面が明るい場合には以下のようになってしまいます。  
![image](https://github.com/user-attachments/assets/ae442104-ef29-466e-9e05-c0b884c9989f)  

そこで、このプロパティを以下のように修正することで背景を暗くすることができます。
```
body { background-color: rgba(0, 0, 0, 0.85); margin: 0px auto; overflow: hidden; }
```
![image](https://github.com/user-attachments/assets/2fbbb24f-b032-466a-830f-ba86ecf7e224)

```0,0,0```の部分を変更することで、黒以外の色に寄せることもできます。必要に応じて変えてみてください。

# 対応状況など
PHOENIXWAN 2022+でのみ動作確認しています。

DAO FP2007だと動かないことが分かっています。(一部キーに対するイベントが特殊なため、対応できない可能性が高いです)  
他にも上手く拾えないコントローラがあったら[作者のTwitter](https://x.com/cold_planet_)に教えていただけると助かります。(ログの送付をお願いするかもしれません)

WebSocketサーバを立ててそこでブラウザソースと通信する仕組みで動くため、
ウイルス対策ソフトのファイアウォールによって通信できない場合があるかもしれません。その際はお手数ですが通信の許可をするようにしてください。
(作者はWindows Defenderしか使っていないため、市販のウイルス対策ソフトに関する質問には答えられません。)

# 今後の予定
また、以下機能を追加するかもしれません。

- IIDX DPでの動作
- ボタン部分に画像を埋め込むための仕組み
- カスタムCSSでできることの追加
  - ボタンや皿部分への画像の追加
  - 押下時の光り方のカスタマイズ

# その他
不具合報告などについては、
本レポジトリのIssuesまたは[作者のTwitter](https://x.com/cold_planet_)へお願いします。

配信へのクレジット表記などは別に必須ではないですが、書いてもらえると喜びます。
```
Otoge Input Viewer
https://github.com/dj-kata/otoge_input_viewer
```
