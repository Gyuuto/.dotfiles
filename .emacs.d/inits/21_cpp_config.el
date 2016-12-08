;; C++ style
(defun c++-mode-hooks()
  (font-lock-add-keywords
    nil '(
      ("\\<\\(alignof\\|alignas\\|constexpr\\|decltype\\|noexcept\\|nullptr\\|static_assert\\|thread_local\\|override\\|final\\)\\>" . 'font-lock-keyword-face)
      )))
(add-hook 'c++-mode-hook
          '(lambda()
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
	     'c++-mode-hooks
             ))

