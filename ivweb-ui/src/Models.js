const stringify = require('csv-stringify');

let startNotification = function() {
  // noop by default
}

const validators = {
  isDateMMDDYYY: function (dateString) {
    // https://stackoverflow.com/questions/6177975/how-to-validate-date-with-format-mm-dd-yyyy-in-javascript/6178341#6178341
    // retrieved 2021-03-23
    // modified for code style and our YY vs YYYY spec

    // First check for the pattern
    if (!/^\d{1,2}\/\d{1,2}\/\d{2}$/.test(dateString)) {
      return false;

    }
    // Parse the date parts to integers
    var parts = dateString.split("/");
    var day = parseInt(parts[1], 10);
    var month = parseInt(parts[0], 10);
    var year = parseInt(parts[2], 10);

    // Check the ranges of month and year
    if (year < 0 || year > 99 || month == 0 || month > 12) {
      return false;
    }

    var monthLength = [ 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ];

    // Adjust for leap years
    if(year % 400 == 0 || (year % 100 != 0 && year % 4 == 0))
        monthLength[1] = 29;

    // Check the range of the day
    return day > 0 && day <= monthLength[month - 1];
  },
  isDoi: function (value) {
    // https://www.crossref.org/blog/dois-and-matching-regular-expressions/
    let id = value.trim();
    const doiA = /^10.\d{4,9}\/[-._;()/:A-Z0-9]+$/i;
    const doiB = /^10.1002\/[^\s]+$/i;
    const doiC = /^10.\d{4}\/\d+-\d+X?(\d+)\d+<[\d\w]+:[\d\w]*>\d+.\d+.\w+;\d$/i;
    return doiA.test(id) || doiB.test(id) || doiC.test(id);
  },
  noSemiColon: function (value) {
    if (typeof value === 'string' && value.includes(';')) {
      return false;
    }
    return true;
  },
  notDate: function (value) {
    return !validators.isDateMMDDYYY(value);
  },
  empty: function (idx, row) {
    return typeof row[idx] !== 'string' || !row[idx] ||
    row[idx].trim() === '';
  },
  yesOrNo: function (value) {
    // this function should work for non-required fields,
    // empty string is allowed
    const index = ['yes', 'no', ''];
    if (typeof value === 'string') {
      const normalized = value.trim().toLowerCase();
      if (index.indexOf(normalized) === -1) {
        return false;
      }
    }
    return true;
  }
}

// todo: i18n support for configurable language messaging
// i.e. messages defined as data rather than strings hardcoded in logic
const messages = {
  custom_article_data: {
    columns: [
      'DOI', 'TOC_SECTION', 'COLLECTION', 'EDITOR', 'CUSTOM', 'CUSTOM_2',
      'CUSTOM_3', 'CITEABLE_ARTICLE', 'IS_OPEN_ACCESS'
    ],
    col_0: {
      valid: validators.isDoi,
      msg: 'DOI field appears to contain non-DOI text string.',
      level: 'warn'
    },
    col_7: {
      valid: validators.yesOrNo,
      msg: 'CITEABLE_ARTICLE: Valid values are "Yes" or "No".',
      level: 'error'
    },
    col_8: {
      valid: validators.yesOrNo,
      msg: 'IS_OPEN_ACCESS: Valid values are "Yes" or "No".',
      level: 'error'
    }
  },
  incorrectHeader: function (expected, actual) {
    return `Incorrect header field: expected ${expected}, found ${actual}`
  },
  nonArrayRow: 'Unexpected format for row, unable to read.',
  wrongColNum: function (expected, actual) {
    return `Incorrect number of columns: expected ${expected}, found ${actual}`
  },
  required: function (column) {
    return `${column} is a required field.`
  },
  requiresOne: function (category) {
    return `At least one ${category} field must have a non-empty value.`
  },
  rejected_articles: {
    columns: [
      'MANUSCRIPT_ID',
      'DATE_OF_REJECTION',
      'REJECT_REASON',
      'TITLE',
      'FIRST_AUTHOR',
      'CORRESPONDING_AUTHOR',
      'CO_AUTHORS',
      'SUBJECT_CATEGORY',
      'EDITOR',
      'SUBMITTED_JOURNAL',
      'ARTICLE_TYPE',
      'KEYWORDS',
      'CUSTOM',
      'FUNDERS',
      'CUSTOM_2',
      'CUSTOM_3',
    ],
    col_1: {
      valid: validators.isDateMMDDYYY,
      msg: 'DATE_OF_REJECTION: Must be date in MM/DD/YYYY format.',
      level: 'error'
    },
    col_2: {
      valid: validators.notDate,
      msg: 'REJECT_REASON: Found date value unexpectedly.',
      level: 'warn'
    },
    col_4: {
      valid: validators.noSemiColon,
      msg: 'FIRST_AUTHOR: Found value with semicolon. Does field include more than one author?',
      level: 'warn'
    }
  }
}

let pipelines = {
  rejected_articles: {
    id: 'rejected_articles',
    name: 'Upload Rejected',
    fileColumns: [
      {
        name: 'MANUSCRIPT_ID',
        px: 100,
        pct: 0.03
      },
      {
        name: 'DATE_OF_REJECTION',
        px: 100,
        pct: 0.03
      },
      {
        name: 'REJECT_REASON',
        px: 100,
        pct: 0.03
      },
      {
        name: 'TITLE',
        px: 350,
        pct: 0.03
      },
      {
        name: 'First_Author',
        px: 200,
        pct: 0.03
      },
      {
        name: 'Corresponding_Author',
        px: 400,
        pct: 0.03
      },
      {
        name: 'Co_Authors',
        px: 300,
        pct: 0.03
      },
      {
        name: 'Subject_Category',
        px: 150,
        pct: 0.03
      },
      {
        name: 'Editor',
        px: 150,
        pct: 0.03
      },
      {
        name: 'Submitted_Journal',
        px: 150,
        pct: 0.03
      },
      {
        name: 'Article_Type',
        px: 150,
        pct: 0.03
      },
      {
        name: 'Keywords',
        px: 150,
        pct: 0.03
      },
      {
        name: 'Custom',
        px: 150,
        pct: 0.03
      },
      {
        name: 'Funders',
        px: 150,
        pct: 0.03
      },
      {
        name: 'Custom_2',
        px: 150,
        pct: 0.03
      },
      {
        name: 'Custom_3',
        px: 150,
        pct: 0.03
      }
    ],
    rowErrorsIndex: {},
    loading: false,
    validator: function (rowCount, row) {
      // rejected_articles validator
      const required = [0, 1, 2, 3, 9];
      const hasChecks = [0, 1, 2, 3, 4, 5, 6, 9];
      const specificChecks = [1, 2, 4];
      if (!pipelines.rejected_articles.loading) {
        console.log('setting load notification...');
        setLoading('rejected_articles', true);
      }
      let errors = rowValidator('rejected_articles', rowCount, row,
        required, hasChecks, specificChecks);

      if (validators.empty(4, row) && validators.empty(5, row) &&
      validators.empty(6, row)) {
        for (var i = 4; i < 7; i++) {
          if (typeof errors[`col_${i}`] === 'undefined') {
            errors[`col_${i}`] = [];
          }
        }
        errors.col_4.push(messages.requiresOne('author'));
        errors.col_5.push(messages.requiresOne('author'));
        errors.col_6.push(messages.requiresOne('author'));
        if (errors.data[4]) {
          errors.data[4].errors.push(messages.requiresOne('author'));
        }
        if (errors.data[5]) {
          errors.data[5].errors.push(messages.requiresOne('author'));
        }
        if (errors.data[6]) {
          errors.data[6].errors.push(messages.requiresOne('author'));
        }
      }
      let finalizedErrors = cleanRowErrorObj(errors, hasChecks);
      if (finalizedErrors.hasErrors) {

      }
      return finalizedErrors;
    }
  },
  custom_article_data: {
    id: 'custom_article_data',
    name: 'Additional Article Metadata',
    fileColumns: [
      {
        name: 'DOI',
        px: 100,
        pct: 0.03
      },
      {
        name: 'TOC_SECTION',
        px: 100,
        pct: 0.03
      },
      {
        name: 'COLLECTION',
        px: 100,
        pct: 0.03
      },
      {
        name: 'EDITOR',
        px: 350,
        pct: 0.03
      },
      {
        name: 'CUSTOM',
        px: 200,
        pct: 0.03
      },
      {
        name: 'CUSTOM_2',
        px: 400,
        pct: 0.03
      },
      {
        name: 'CUSTOM_3',
        px: 300,
        pct: 0.03
      },
      {
        name: 'CITEABLE_ARTICLE',
        px: 150,
        pct: 0.03
      },
      {
        name: 'IS_OPEN_ACCESS',
        px: 150,
        pct: 0.03
      }
    ],
    rowErrorsIndex: {},
    validationInProgress: false,
    validator: function (rowCount, row) {
      // custom_article_data validator
      const required = [0];
      const hasChecks = [0, 7, 8];
      const specificChecks = [0, 7, 8];
      let errors = rowValidator('custom_article_data', rowCount, row,
        required, hasChecks, specificChecks);
      let finalizedErrors = cleanRowErrorObj(errors, hasChecks);
      if (finalizedErrors.hasErrors) {

      }
      return finalizedErrors;
    }
  }
}

export function setLoading(pipeline_id, loading) {
  let logoElems = document && document.getElementsByClassName('hwp-loading-icon');

  if (pipelines[pipeline_id]) {
    pipelines[pipeline_id].loading = loading;
  }

  if (loading) {
    console.log('adding loading class: ', logoElems.length);
    for (let i = 0; i < logoElems.length; i++) {
      if (logoElems[i].classList) {
        logoElems[i].classList.remove('not-loading');
      }
    }
  }
  else {
    console.log('removing loading class');
    for (let i = 0; i < logoElems.length; i++) {
      if (logoElems[i].classList) {
        logoElems[i].classList.add('not-loading');
      }
    }
  }
}

function rowValidator(pipelineId, rowCount, row, required, hasChecks,
specificChecks) {
  let errors = {
    data: row.map((field) => {
      return {
        data: field,
        errors: []
      }
    }),
    row: [],
    rowCount: rowCount
  };
  let columns = messages[pipelineId].columns;

  if (typeof pipelines[pipelineId] === 'undefined') {
    return errors;
  }

  if (!Array.isArray(row)) {
    errors.row.push(messages.nonArrayRow);
    return errors;
  }
  else if (rowCount === 1) {
    // validate header, skip additional checks
    return validateHeaderRow(columns, row, errors);
  }
  else if (row.length !== columns.length) {
    errors.row.push(messages.wrongColNum(columns.length, row.length))
  }

  for (let i = 0; i < hasChecks.length; i++) {
    errors[`col_${hasChecks[i]}`] = [];
  }

  for (let i = 0; i < required.length; i++) {
    if (validators.empty(required[i], row)) {
      if (typeof errors[`col_${required[i]}`] === 'undefined') {
        errors[`col_${required[i]}`] = [];
      }
      errors[`col_${required[i]}`]
        .push(messages.required(columns[required[i]]));
      if (errors.data[required[i]] && errors.data[required[i]].errors) {
        errors.data[required[i]].errors
          .push(messages.required(columns[required[i]]))
      }
    }
  }

  for (let i = 0; i < specificChecks.length; i++) {
    if (typeof messages[pipelineId][`col_${specificChecks[i]}`] === 'undefined' ||
    messages[pipelineId][`col_${specificChecks[i]}`]
    .valid(row[specificChecks[i]])) {
      continue;
    }
    if (typeof errors[`col_${specificChecks[i]}`] === 'undefined') {
      errors[`col_${specificChecks[i]}`] = [];
    }
    errors[`col_${specificChecks[i]}`]
      .push(messages[pipelineId][`col_${specificChecks[i]}`].msg)
    if (errors.data[specificChecks[i]]) {
      errors.data[specificChecks[i]].errors
        .push(messages[pipelineId][`col_${specificChecks[i]}`].msg)
    }
  }

  return errors;
}

function validateHeaderRow(columns, row, errors) {
  let hasErrors = false;
  if (columns.length !== row.length) {
    errors.row.push(messages.wrongColNum(columns.length, row.length));
    hasErrors = true;
  }
  for (let i = 0; i < row.length && i < columns.length; i++) {
    if (typeof row[i] !== 'string') {
      errors.data[i].errors
        .push(messages.required(`Header field: ${columns[i]}`));
      hasErrors = true;
      continue;
    }
    if (row[i].toUpperCase() !== columns[i].toUpperCase()) {
      errors.data[i].errors
        .push(messages.incorrectHeader(columns[i], row[i]));
      hasErrors = true;
    }
  }
  if (hasErrors) {
    errors.data = errors.data.map((item) => {
      return {...item, rowHasErrors: hasErrors}
    })
  }
  return errors;
}

function cleanRowErrorObj(errors, hasChecks) {
  let hasErrors = false;
  for (let i = 0; i < hasChecks.length; i++) {
    if (Array.isArray(errors[`col_${hasChecks[i]}`]) &&
    errors[`col_${hasChecks[i]}`].length > 0) {
      hasErrors = true;
    }
  }
  if (errors.row.length > 0) {
    hasErrors = true;
  }
  errors.hasErrors = hasErrors;
  if (hasErrors) {
    errors.data = errors.data.map((item) => {
      return {...item, rowHasErrors: hasErrors}
    })
  }
  return errors;
}

export function pipelineById(pipelineId) {
  if (typeof pipelines[pipelineId] !== 'undefined') {
    console.log('Initializing pipeline: ', pipelineId);
    console.log(pipelines[pipelineId]);
    return pipelines[pipelineId];
  }
  else {
    console.log('Failed to match supplied pipelineId in model:');
    console.log(pipelineId);
    return {
      id: '',
      name: 'Error - pipeline not configured',
      fileColumns: [],
      validator: function (pipelineId, rowCount, row, required, hasChecks,
      specificChecks) {
        if (!Array.isArray(row)) {
          row = [];
        }
        let errors = {
          data: row.map((field) => {
            return {
              data: field,
              errors: []
            }
          }),
          row: [],
          rowCount: rowCount
        };
        return cleanRowErrorObj(errors);
      }
    }
  }
}

export function resetPipeline(pipelineId) {
  pipelines[pipelineId].rowErrorsIndex = {};
  pipelines[pipelineId].validationInProgress = false;
}

export function generateTsv(rows) {
  return new Promise((resolve, reject) => {
    const stringifier = stringify({
      delimiter: '\t'
    });
    let rowStrings = [];
    let errors = [];
    stringifier.on('readable', function () {
      let rowString;
      while (rowString = stringifier.read()) {
        rowStrings.push(rowString);
      }
    });

    stringifier.on('error', function (err) {
      console.log('Error on csv stringify: ', err);
      errors.push(err);
    });

    stringifier.on('finish', function () {
      const tsv = new Blob(rowStrings, {});
      resolve(tsv);
    });

    for (let i = 0; i < rows.length; i++) {
      stringifier.write(rows[i]);
    }
    stringifier.end();

  });
}

export function Store() {
  this.state = {
    parsedRows: [],
    rows: [],
    rowCount: [],
    rowErrors: [],
    rowErrorsIndex: {},
    textErrors: []
  };

  this.setState = (newState) => {
    Object.assign(this.state, newState);
  }

  this.reset = () => {
    this.state = {
      parsedRows: [],
      rows: [],
      rowCount: [],
      rowErrors: [],
      rowErrorsIndex: {},
      textErrors: []
    };
  }
}
