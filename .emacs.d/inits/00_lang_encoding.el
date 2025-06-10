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
;; (add-to-list 'default-frame-alist '(font . "rictydiminished-12"))

(when (string= window-system "w32")
  (if (find-font (font-spec :name "UDEV Gothic"))
      (progn
        (create-fontset-from-ascii-font "UDEV Gothic JPDOC-11:weight=normal:slant=normal" nil "myfont"))
    (progn
      (create-fontset-from-ascii-font "consolas-11:weight=normal:slant=normal" nil "myfont")
      (add-to-list 'default-frame-alist '(font . "Consolas-11"))

      (set-fontset-font "fontset-myfont" 'japanese-jisx0208 "メイリオ-10:weight=normal:slant=normal" nil 'append)
      (set-fontset-font "fontset-myfont" 'japanese-jisx0212 "メイリオ-10:weight=normal:slant=normal" nil 'append)
      )
    )

  (add-to-list 'default-frame-alist '(font . "fontset-myfont"))
)

