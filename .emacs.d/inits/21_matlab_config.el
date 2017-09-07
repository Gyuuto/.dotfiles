;; Matlab style
(add-hook 'octave-mode-hook
          '(lambda()
             (c-set-style "stroustrup")
             (c-set-offset 'inline-open 0)
             (c-set-offset 'topmost-intro 0)
             (c-set-offset 'defun-block-intro '+)
             (c-set-offset 'statement 0)
             (c-set-offset 'statement-block-intro '+)
             (c-toggle-hungry-state 1)
             (setq tab-width 4)
             (setq c-basic-offset tab-width)
             ))

;; matlab style
(autoload 'octave-mode "octave-mod" nil t)
(add-hook 'octave-mode-hook
	  (lambda ()
	    (abbrev-mode 1)
	    (auto-fill-mode 1)
	    (define-key octave-mode-map "\C-m"
	      'octave-reindent-then-newline-and-indent)
	    (if (eq window-system 'x)
		(font-lock-mode 1))))

;; setup matlab-mode
(require 'matlab)
(setq matlab-shell-command "/Applications/MATLAB_R2015b.app/bin/matlab"
      matlab-indent-level 4
      matlab-indent-function-body t
      matlab-highight-cross-function-variables t
      matlab-return-add-semicolon t
      matlab-show-mlint-warnings t
      matlab-fill-code nil
      mlint-programs '("/Applications/MATLAB_R2015b.app/bin/maci64/mlint")
      matlab-mode-install-path (list (concat system_path "/.emacs.d/elisp/matlab-mode"))
      )
