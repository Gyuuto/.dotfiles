;=======================================================================
;フレームサイズ・位置・色など
;=======================================================================
(setq default-frame-alist
      (append (list '(foreground-color . "gray")
		    '(background-color . "Black")
		    '(border-color . "black")
		    '(mouse-color . "white")
		    '(cursor-color . "white")
		    '(width . 100)  
		    '(height . 40) 
		    )
	      default-frame-alist))
;;

;;; スタートアップを出さない
(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(ecb-options-version "2.32")
 '(indent-region-mode t)
 '(inhibit-startup-screen t)
 '(magit-branch-arguments nil)
 '(majmodpri-mode-priorities
   (quote
    (cperl-mumamo-mode csound-sgml-mumamo-mode django-nxhtml-mumamo-mode django-html-mumamo-mode embperl-nxhtml-mumamo-mode embperl-html-mumamo-mode eruby-nxhtml-mumamo-mode eruby-html-mumamo-mode genshi-nxhtml-mumamo-mode genshi-html-mumamo-mode jsp-nxhtml-mumamo-mode jsp-html-mumamo-mode laszlo-nxml-mumamo-mode metapost-mumamo-mode mjt-nxhtml-mumamo-mode mjt-html-mumamo-mode noweb2-mumamo-mode perl-mumamo-mode smarty-nxhtml-mumamo-mode smarty-html-mumamo-mode nxhtml-mumamo-mode html-mumamo-mode nxml-mumamo-mode nxml-mode js-mode rhtml-mode)))
 '(nxhtml-global-minor-mode t)
 '(nxhtml-global-validation-header-mode t)
 '(nxhtml-skip-welcome t)
 '(package-selected-packages
   (quote
    (flycheck-irony flycheck undo-tree markdown-mode magit font-lock+ dash-functional))))


(when (not (eq window-system nil))
  ;; メニューバーを消す
  (menu-bar-mode 0)
  ;; ツールバーを消す
  (tool-bar-mode 0)
)

;;; 領域の色付け
(setq transient-mark-mode t)

;;文字の色つけ
(global-font-lock-mode t)

;;カーソルのある行番号・桁番号を表示
(setq line-number-mode t)
(setq column-number-mode t)

;;日本語infoの文字化け防止
(auto-compression-mode t)

;;フレームのタイトル指定
(setq frame-title-format
    (concat "%b - emacs@" system-name))

;;時計を表示
(display-time)

;;; リージョンに色を付ける
(setq transient-mark-mode t)
(set-face-background 'region "darkgreen")

;;; 対応する括弧を光らせる
(show-paren-mode)

;; change theme
(load-theme 'tango-dark t)

;; highlight current line
(defface hlline-face
  '((((class color)
      (background dark))
     (:background "dark slate gray"))
    (((class color)
      (background light))
     (:background  "#98FB98"))
    (t
     ()))
  "*Face used by hl-line.")
(setq hl-line-face 'hlline-face)
(global-hl-line-mode)

(require 'ansi-color)
(defun display-ansi-colors ()
  (interactive)
  (ansi-color-apply-on-region (point-min) (point-max)))
