;; C# style
;(fa-config-default)
(add-hook 'csharp-mode-hook
          (lambda()
            (c-set-style "stroustrup")
            (c-set-offset 'inline-open 0)
            (c-set-offset 'topmost-intro 0)
            (c-set-offset 'defun-block-intro '+)
            (c-set-offset 'statement 0)
            (c-set-offset 'statement-block-intro '+)
            (c-set-offset 'inlambda 0)
            (c-set-offset 'block-open 0)
            (c-set-offset 'innamespace 0)
            (c-toggle-hungry-state 1)
            (setq tab-width 4)
            (setq c-basic-offset tab-width)
            (yas-minor-mode)
            'cshap-mode-hooks
            ))
