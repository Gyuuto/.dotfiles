;; 自動インデント機能
(add-hook 'c-mode-common-hook
          '(lambda ()
             ;; RET キーで自動改行+インデント
             (define-key c-mode-base-map "\C-m" 'newline-and-indent)
	     ))

(setq auto-mode-alist
      ;;; 拡張子とモードの対応
      (append
       '(("\\.c$" . c-mode))
       '(("\\.h$" . c-mode))
       '(("\\.cl$" . c-mode))
       '(("\\.cpp$" . c++-mode))
       '(("\\.glsl$" . c++-mode))
       '(("\\.cxx$" . c++-mode))
       '(("\\.hpp$" . c++-mode))
       '(("\\.java$" . java-mode))
       '(("\\.ml[iylp]?$" . tuareg-mode))
       '(("\\.cmake$" . cmake-mode))
       '(("\\CMakeLists.txt$" . cmake-mode))
       '(("\\.txt$" . text-mode))
       '(("\\.tex$" . yatex-mode))
       '(("\\.m$" . matlab-mode))
       '(("\\.md$" . markdown-mode))
       '(("\\.html$" . web-mode)) 
       '(("\\.xml$" . web-mode))
       '(("\\.css$" . web-mode))
       '(("\\.php$" . web-mode))
       '(("\\.jsp$" . web-mode))
       '(("\\.js$" . web-mode)) 
       '(("\\.jsx$" . web-mode)) 
       auto-mode-alist)
)

(add-hook 'find-file-not-found-hooks 'auto-insert)
;;
