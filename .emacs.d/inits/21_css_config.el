;; css-modeの設定
(require 'css-mode)
(setq auto-mode-alist
      (cons '("\\.css\\'" . css-mode) auto-mode-alist))
(setq cssm-indent-function #'cssm-c-style-indenter)
(add-hook 'css-mode-hook
	  (lambda()
                                        ;(define-key cssm-mode-map "\r" 'newline-and-indent)
                                        ;(setq indent-tabs-mode t)
                                        ;(setq cssm-indent-level 4)
                                        ;(setq tab-width 4)
            )
)


;;javascript
(autoload 'js-mode "js" nil t)
(add-hook 'js-mode-hook
	  (lambda()
            (setq tab-width 4)
            (c-set-offset 'inline-open 0)
            (c-set-offset 'topmost-intro 0)
            (c-set-offset 'defun-block-intro '+)
            (c-set-offset 'statement 0)
            (c-set-offset 'statement-block-intro '+)
            (c-toggle-hungry-state 1)
            ))
