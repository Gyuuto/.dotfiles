;======================================================================
; 言語・文字コード関連の設定
;======================================================================
(set-language-environment 'Japanese)
(prefer-coding-system 'utf-8)

;;(set-language-environment 'utf-8)
;;(set-terminal-coding-system 'utf-8)
;;(set-keyboard-coding-system 'utf-8)
;;(set-buffer-file-coding-system 'utf-8)
;;(setq default-buffer-file-coding-system 'utf-8)
;;(prefer-coding-system 'utf-8)
;;(set-default-coding-systems 'utf-8)
;;(setq file-name-coding-system 'shift-jis)
;;(setq file-name-coding-system 'utf-8)
;;
;=======================================================================
;フォント
;=======================================================================
(when (eq window-system 'w32)
  (set-face-attribute 'default nil
                      :family "Consolas"
		      :height 105)
  (set-fontset-font nil 'japanese-jisx0208 (font-spec :family "メイリオ"))
)
(when (eq window-system 'ns)
  (set-face-attribute 'default nil
                      :family "Consolas"
		      :height 125)
  (set-fontset-font nil 'japanese-jisx0208 (font-spec :family "Hiragino Kaku Gothic ProN"))
)

;(cond ((string= window-system "w32")
;       (create-fontset-from-ascii-font
;	"-outline-メイリオ-normal-r-normal-normal-12-*-*-*-*-*-iso8859-1"
;	nil "メイリオ")
;      
;       (create-fontset-from-ascii-font
;	"-outline-メイリオ-normal-r-normal-normal-14-*-*-*-*-*-iso8859-1"
;	nil "メイリオ")
;       
;       (set-fontset-font "fontset-メイリオ"
;			 'japanese-jisx0208
;			 '("メイリオ*" . "jisx0208-sjis"))
;       (set-fontset-font "fontset-メイリオ"
;			 'katakana-jisx0201
;			 '("メイリオ*" . "jisx0201-katakana"))
;))
