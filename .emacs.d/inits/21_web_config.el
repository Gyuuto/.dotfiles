(require 'web-mode)

(setq web-mode-enable-auto-closing t)
(setq web-mode-enable-auto-pairing t)

(setq web-mode-auto-close-style 2)
(setq web-mode-tag-auto-close-style 2)

(add-hook 'web-mode-hook
          (lambda()
            (setq tab-width 4)
            (setq indent-tabs-mode t)
            )
          )
