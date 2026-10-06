module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/scripts/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        "tk-error": "rgb(var(--c-error-rgb) / <alpha-value>)",
        "tk-surface": "rgb(var(--c-surface-rgb) / <alpha-value>)",
        "tk-ink": "rgb(var(--c-ink-rgb) / <alpha-value>)",
        "tk-primary": "rgb(var(--c-primary-rgb) / <alpha-value>)",
        "tk-brass": "rgb(var(--c-brass-rgb) / <alpha-value>)",
        "tk-paper": "rgb(var(--c-paper-rgb) / <alpha-value>)",
        "tk-line": "rgb(var(--c-line-rgb) / <alpha-value>)",
        "tk-ink-muted": "rgb(var(--c-ink-muted-rgb) / <alpha-value>)",
        "tk-success": "rgb(var(--c-success-rgb) / <alpha-value>)",
        "tk-primary-700": "rgb(var(--c-primary-700-rgb) / <alpha-value>)",
      },
    },
  },
  plugins: [],
};
