;; 自動インデント機能
(add-hook 'c-mode-common-hook
          (lambda ()
            ;; RET キーで自動改行+インデント
            (define-key c-mode-base-map "\C-m" 'newline-and-indent)
            ))

(setq-default indent-tabs-mode nil)
(setq-default tab-width 4)

(setq auto-mode-alist
      ;;; 拡張子とモードの対応
      (append
       '(("\\.c$" . c-mode))
       '(("\\.h$" . c++-mode))
       '(("\\.cl$" . c-mode))
       '(("\\.cu$" . cuda-mode))
       '(("\\.cpp$" . c++-mode))
       '(("\\.glsl$" . c++-mode))
       '(("\\.cxx$" . c++-mode))
       '(("\\.hpp$" . c++-mode))
       '(("\\.cs$" . csharp-mode))
       '(("\\.java$" . java-mode))
       '(("\\.ml[iylp]?$" . tuareg-mode))
       '(("\\.cmake$" . cmake-mode))
       '(("\\CMakeLists.txt$" . cmake-mode))
       '(("\\.txt$" . text-mode))
       '(("\\.tex$" . yatex-mode))
       '(("\\.m$" . matlab-mode))
       '(("\\.md$" . markdown-mode))
       '(("\\.rs$" . rust-mode))
       '(("\\.html$" . web-mode)) 
       '(("\\.jade$" . jade-mode)) 
       '(("\\.xml$" . web-mode))
       '(("\\.css$" . web-mode))
       '(("\\.php$" . web-mode))
       '(("\\.jsp$" . web-mode))
       '(("\\.js$" . web-mode)) 
       '(("\\.ts$" . web-mode)) 
       '(("\\.jsx$" . web-mode)) 
       '(("\\.py$" . python-mode))
       '(("\\.vue$" . vue-mode))
       auto-mode-alist)
)

(add-hook 'find-file-not-found-hooks 'auto-insert)

(require 'highlight-symbol)
(setq highlight-symbol-colors '("LightSeaGreen" "HotPink" "SlateBlue1" "DarkOrange" "SpringGreen1" "tan" "DodgerBlue1"))
(setq highlight-symbol-idle-delay 1.0)
(add-hook 'prog-mode-hook 'highlight-symbol-mode)
(add-hook 'prog-mode-hook 'highlight-symbol-nav-mode)

(require 'expand-region)
(global-set-key (kbd "C-,") 'er/expand-region)

;; enclosed selected region
(defun region-to-single-quote ()
  (interactive)
  (quote-formater "'%s'" "^\\(\"\\).*" ".*\\(\"\\)$"))
(defun region-to-double-quote ()
  (interactive)
  (quote-formater "\"%s\"" "^\\('\\).*" ".*\\('\\)$"))
(defun region-to-bracket ()
  (interactive)
  (quote-formater "\(%s\)" "^\\(\\[\\).*" ".*\\(\\]\\)$"))
(defun region-to-square-bracket ()
  (interactive)
  (quote-formater "\[%s\]" "^\\(\(\\).*" ".*\\(\)\\)$"))
(defun quote-formater (quote-format re-prefix re-suffix)
  (if mark-active
      (let* ((region-text (buffer-substring-no-properties (region-beginning) (region-end)))
             (replace-func (lambda (re target-text)(replace-regexp-in-string re "" target-text nil nil 1)))
             (text (funcall replace-func re-suffix (funcall replace-func re-prefix region-text))))
        (delete-region (region-beginning) (region-end))
        (insert (format quote-format text)))
    (error "Not Region selection")))

;; (require 'region-bindings-mode)
;; (region-bindings-mode-enable)
;; (define-key region-bindings-mode-map (kbd "M-'") 'region-to-single-quote)
;; (define-key region-bindings-mode-map (kbd "M-\"") 'region-to-double-quote)
;; (define-key region-bindings-mode-map (kbd "M-9") 'region-to-bracket)
;; (define-key region-bindings-mode-map (kbd "M-[") 'region-to-square-bracket)

;; emphasize the colors of parenthesis in rainbow-delimiters
(require 'rainbow-delimiters)
(add-hook 'prog-mode-hook 'rainbow-delimiters-mode)

(require 'cl-lib)
(require 'color)
(defun rainbow-delimiters-using-stronger-colors ()
  (interactive)
  (cl-loop
   for index from 1 to rainbow-delimiters-max-face-count
   do
   (let ((face (intern (format "rainbow-delimiters-depth-%d-face" index))))
     (cl-callf color-saturate-name (face-foreground face) 30))))
(add-hook 'emacs-startup-hook 'rainbow-delimiters-using-stronger-colors)

;; (require 'lsp-ui)
;; ;; (global-unset-key (kbd "C-M-."))
;; (global-set-key (kbd "M-?") (lambda () (interactive)
;;                               ;; (setq lsp-ui-peek-list-width (/ (window-pixel-width) 2))
;;                               (lsp-ui-peek-find-references)))

;; (global-set-key (kbd "C-c C-SPC") (lambda () (interactive)
;;                                     (lsp-signature-activate)))

;; ;; adjust peek-ui-width manually
;; ;; but these are inconvinience...
;; (define-key lsp-ui-mode-map (kbd "M-[ 1 ; 5 l") (lambda () (interactive)
;;                                                   (setq lsp-ui-peek-list-width (* lsp-ui-peek-list-width 1.5))
;;                                                   (lsp-ui-peek-find-references)))
;; (define-key lsp-ui-mode-map (kbd "M-[ 1 ; 5 n") (lambda () (interactive)
;;                                                   (setq lsp-ui-peek-list-width (/ lsp-ui-peek-list-width 1.5))
;;                                                   (lsp-ui-peek-find-references)))
