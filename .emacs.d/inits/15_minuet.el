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

  (let* ((server my/llm-server-latest-light-coder))
    (plist-put minuet-openai-compatible-options
               :end-point (my/llm-server-make-endpoint server))
    (plist-put minuet-openai-compatible-options
               :name "ollama")
    (plist-put minuet-openai-compatible-options
               :api-key (my/llm-server-api-key server))
    (plist-put minuet-openai-compatible-options
               :model (format "%s" (car (my/llm-server-model server)))))
)

