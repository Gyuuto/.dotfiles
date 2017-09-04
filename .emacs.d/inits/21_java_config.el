(require 'meghanada)
(add-hook 'java-mode-hook
          '(lambda()
	     ;; meghanada-mode on
	     (meghanada-mode t)
             (c-set-style "stroustrup")
             (setq indent-tabs-mode t) 
             (c-set-offset 'inline-open 0)
             (c-set-offset 'topmost-intro 0)
             (c-set-offset 'defun-block-intro '+)
             (c-set-offset 'statement 0)
             (c-set-offset 'statement-block-intro '+)
             (c-toggle-hungry-state 1)
             (setq tab-width 4)
             (setq c-basic-offset tab-width)
             ))

(push 'java-mode irony-supported-major-modes)
