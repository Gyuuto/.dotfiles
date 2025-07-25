;; markdown mode
(require 'markdown-mode)
(autoload 'markdown-mode "markdown-mode" "Major mode for editing Markdown files" t)

(add-hook 'markdown-mode-hook
          (lambda()
            (setq tab-width 4)
            ))

;; don't change font in codeblocks
(set-face-attribute 'markdown-code-face nil :inherit 'default :foreground "#00ccff")

(bind-keys :map markdown-mode-map
           ("M-p" . outline-previous-visible-heading)
           ("M-n" . outline-next-visible-heading)
           )
