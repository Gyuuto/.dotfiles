;======================================================================
; 言語・文字コード関連の設定
;======================================================================
(set-language-environment 'Japanese)

(prefer-coding-system 'utf-8)
(set-coding-system-priority 'utf-8)
(when (eq window-system 'w32)
  (setq default-process-coding-system '(utf-8 . sjis)))

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

(when (string= window-system "w32")
  (if (find-font (font-spec :name "UDEV Gothic JPDOC"))
      ;; 【パターンA】UDEV Gothic がある場合
      (progn
        ;; 1. 基本となるフォント（英数字・日本語）を設定
        (add-to-list 'default-frame-alist '(font . "UDEV Gothic JPDOC-11"))
        (set-frame-font "UDEV Gothic JPDOC-11" nil t)

        ;; 2. Nerd Fonts 領域を「NF版」に割り当て
        (set-fontset-font "fontset-default" '(#xE000 . #xF8FF) (font-spec :family "UDEV Gothic NF"))
        (set-fontset-font "fontset-default" '(#xF0000 . #xFFFFD) (font-spec :family "UDEV Gothic NF"))

        ;; 絵文字（emoji）スクリプト領域に Windows 標準の絵文字フォントを明示
        (set-fontset-font "fontset-default" 'emoji (font-spec :family "Segoe UI Emoji")))

    ;; 【パターンB】UDEV Gothic がない場合の保険
    (progn
      (add-to-list 'default-frame-alist '(font . "Consolas-11"))
      (set-frame-font "Consolas-11" nil t)
      (set-fontset-font "fontset-default" 'japanese-jisx0208 "メイリオ-10:weight=normal:slant=normal" nil 'append)
      (set-fontset-font "fontset-default" 'japanese-jisx0212 "メイリオ-10:weight=normal:slant=normal" nil 'append)))
  )
