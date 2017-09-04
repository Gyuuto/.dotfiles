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
       '(("\\.cpp$" . c++-mode))
       '(("\\.glsl$" . c++-mode))
       '(("\\.cxx$" . c++-mode))
       '(("\\.hpp$" . c++-mode))
       '(("\\.java$" . java-mode))
       '(("\\.html$" . nxhtml-mumamo-mode)) 
       '(("\\.xml$" . nxhtml-mumamo-mode))
       '(("\\.ml[iylp]?$" . tuareg-mode))
       '(("\\.php$" . nxhtml-mumamo-mode))
       '(("\\.css$" . css-mode))
       '(("\\.cmake$" . cmake-mode))
       '(("\\CMakeLists.txt$" . cmake-mode))
       '(("\\.txt$" . text-mode))
       '(("\\.tex$" . yatex-mode))
       '(("\\.m$" . matlab-mode))
       '(("\\.md$" . markdown-mode))
       '(("\\.rs$" . rust-mode))
       auto-mode-alist)
)

;; テンプレート
(require 'autoinsert)
(cond ((string= window-system "w32")
       (setq auto-insert-directory "C:/Users/Yuto Inoue/Desktop/Programming/")
       )
      ((eq 1 1)
       (setq auto-insert-directory "~/Documents/Programming/")
       )
)
(setq auto-insert-alist
      (append  '( ("\\.cpp$" . "C++/template.cpp")
                ) auto-insert-alist))

(add-hook 'find-file-not-found-hooks 'auto-insert)
;;
