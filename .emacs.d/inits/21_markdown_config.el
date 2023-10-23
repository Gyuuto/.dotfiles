;; markdown mode
(autoload 'markdown-mode "markdown-mode" "Major mode for editing Markdown files" t)

(add-hook 'markdown-mode-hook
          (lambda()
            (setq tab-width 4)
            ))
