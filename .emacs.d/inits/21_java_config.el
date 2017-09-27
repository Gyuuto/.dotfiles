(defadvice c-lineup-arglist (around my activate)
  "Improve indentation of continued Java 8 lambda function opened as argument."
  (setq ad-return-value
        (if (and (equal major-mode 'java-mode)
                 (ignore-errors
                   (save-excursion
                     (goto-char (c-langelem-pos langelem))
                     ;; Detect "->{"
                     ;;   and with unclosed brace.
                     (looking-at ".*[ \t]*->[ \t]*{[^}]*$"))))
            0                           ; no additional indent
          ad-do-it)))

(add-hook 'java-mode-hook
          (lambda()
            (c-set-style "stroustrup")
            (c-set-offset 'inline-open 0)
            (c-set-offset 'topmost-intro 0)
            (c-set-offset 'defun-block-intro '+)
            (c-set-offset 'statement 0)
            (c-set-offset 'statement-block-intro '+)
            (c-toggle-hungry-state 1)
            (setq tab-width 4)
            (setq c-basic-offset tab-width)
            (setq indent-tabs-mode t)
            ))

(unless (string= window-system "w32")
  (progn
     (require 'meghanada)
     (add-hook 'java-mode-hook
               (lambda()
                  ;; meghanada-mode on
                  (meghanada-mode t)
                  ))
     )
  )

(require 'irony)
(require 'company-irony)
(push 'java-mode irony-supported-major-modes)
