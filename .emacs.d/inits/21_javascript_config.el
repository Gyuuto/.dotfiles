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
