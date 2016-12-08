;; nxhtml-mumamo-modeの設定
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(mumamo-background-chunk-major ((((class color) (min-colors 8)) (:background "*"))))
 '(mumamo-background-chunk-submode ((((class color) (min-colors 8)) (:background "*"))))
 '(mumamo-background-chunk-submode1 ((((class color) (min-colors 88) (background dark)) (:background "black"))))
 '(mumamo-background-chunk-submode2 ((((class color) (min-colors 88) (background dark)) (:background "black"))))
 '(mumamo-background-chunk-submode3 ((((class color) (min-colors 88) (background dark)) (:background "black"))))
 '(mumamo-background-chunk-submode4 ((((class color) (min-colors 88) (background dark)) (:background "black")))))
(add-hook 'nxml-mode-hook
	  '(lambda()
	     (define-key nxml-mode-map "\r" 'newline-and-indent)
	     (setq indent-tabs-mode t)
	     (setq nxml-slash-auto-complete-flag t)
	     (setq nxml-child-indent 4)
	     (setq nxml-attribute-indent 4)
	     (setq tab-width 4)
	     (setq nxml-basic-offset tab-width)
             ))

;; yahtml-modeの設定
(autoload 'yahtml-mode "yahtml" "Yet Another html mode" t)
(add-hook 'yahtml-mode-hook
	  (lambda()
	    (setq indent-line-function 'yahtml-indent-line)
	    (define-key yahtml-mode-map "\C-m" 'reindent-then-newline-and-indent)
	    )
	  )
