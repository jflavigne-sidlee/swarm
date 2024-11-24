exports.plugins = [
  require('remark-preset-lint-recommended'),
  require('remark-preset-lint-markdown-style-guide'),
  require('remark-gfm'),
  require('remark-validate-links'),
  [require('remark-lint-maximum-line-length'), false],
  [require('remark-lint-no-undefined-references'), true],
  [require('remark-lint-no-empty-sections'), true],
  [require('remark-lint-heading-increment'), true],
  [require('remark-lint-no-duplicate-headings-in-section'), true],
  [require('remark-lint-table-pipe-alignment'), true],
  [require('remark-lint-table-cell-padding'), true]
] 