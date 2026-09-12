;; -*- lexical-binding: t; -*-

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

(when (eq window-system 'w32)
  (if (find-font (font-spec :family "UDEV Gothic NF"))
      ;; UDEV Gothic がある場合
      (progn
        ;; 基本フォント
        (add-to-list 'default-frame-alist
                     '(font . "UDEV Gothic NF-10.5"))
        (set-face-attribute 'default nil
                            :family "UDEV Gothic NF"
                            :height 120)

        ;; 絵文字
        (set-fontset-font "fontset-default"
                          'emoji
                          (font-spec :family "Segoe UI Emoji" :height 105)))

    ;; UDEV Gothic がない場合
    (progn
      (add-to-list 'default-frame-alist
                   '(font . "Consolas-10.5"))
      (set-face-attribute 'default nil
                          :family "Consolas"
                          :height 105)
      (set-fontset-font "fontset-default"
                        'japanese-jisx0208
                        (font-spec :family "メイリオ"
                                   :height 105)
                        nil 'append)
      (set-fontset-font "fontset-default"
                        'japanese-jisx0212
                        (font-spec :family "メイリオ"
                                   :height 105)
                        nil 'append))))

;; (when (eq window-system 'w32)
;;   (when (find-font (font-spec :family "UDEV Gothic NF"))
;;     (add-to-list 'default-frame-alist
;;                  '(font . "UDEV Gothic NF-10.5"))
;;     (set-frame-font "UDEV Gothic NF-10.5" nil t)

;;     ;; 絵文字
;;     (set-fontset-font "fontset-default"
;;                       'emoji
;;                       (font-spec :family "Segoe UI Emoji"))))
