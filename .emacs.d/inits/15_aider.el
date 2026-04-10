(use-package aidermacs
  :ensure t
  :bind (
         ("C-c C-a" . aidermacs-transient-menu))

  :config
  (let* ((chat-server my/llm-server-latest-light-chat)
         (coder-server my/llm-server-latest-light-coder))
    (let* ((model-name (format "openai/%s" (car (my/llm-server-model coder-server)))))
      (setq aidermacs-extra-args
            `("--model" ,model-name
              "--no-auto-commits"
              "--no-auto-accept-architect"
              "--subtree-only")))
    (setenv "OPENAI_API_KEY" "TERM")
    (setenv "OPENAI_API_BASE" (my/llm-server-make-base chat-server)))

  ;; 文字化け防止
  ;; TODO: check these vars affect to others
  (add-to-list 'process-coding-system-alist '("aider" . (utf-8 . utf-8)))
  (setenv "PYTHONIOENCODING" "utf-8")
  (setenv "LANG" "ja_JP.UTF-8")
  )
