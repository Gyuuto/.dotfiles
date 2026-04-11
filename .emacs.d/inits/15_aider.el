(use-package aidermacs
  :ensure t
  :bind (
         ("C-c C-a" . aidermacs-transient-menu))

  :config
  (let* ((coder-server my/llm-server-agent-coder))
    (let* ((model-name (format "openai/%s" (car (my/llm-server-model coder-server))))
           (api-base (my/llm-server-make-base coder-server))
           (api-key "TERM"))
      (setq aidermacs-extra-args
            `("--model" ,model-name
              "--openai-api-base" ,api-base
              "--openai-api-key" ,api-key
              "--no-auto-accept-architect"
              "--subtree-only"))))

  ;; 文字化け防止
  ;; TODO: check these vars affect to others
  (add-to-list 'process-coding-system-alist '("aider" . (utf-8 . utf-8)))
  (setenv "PYTHONIOENCODING" "utf-8")
  (setenv "LANG" "ja_JP.UTF-8")
  )
