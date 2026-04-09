(use-package minuet
  :bind
  (("C-c <tab>" . #'minuet-show-suggestion)
   ("C-c p" . #'minuet-previous-suggestion)
   ("C-c n" . #'minuet-next-suggestion)
   ("C-c a" . #'minuet-accept-suggestion))

  :init
  ;; (add-hook 'prog-mode-hook #'minuet-auto-suggestion-mode)

  :config
  (setq minuet-provider 'openai-compatible)
  (setq minuet-n-completions 5)
  (setq minuet-context-window 512)
  (setq minuet-request-timeout 15)

  (plist-put minuet-openai-compatible-options
             :end-point "")
  (plist-put minuet-openai-compatible-options
             :name "")
  (plist-put minuet-openai-compatible-options
             :api-key "TERM")
  (plist-put minuet-openai-compatible-options
             :model "")
)

