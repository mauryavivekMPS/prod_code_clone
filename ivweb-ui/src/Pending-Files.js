import './Pending-Files.css';
import React, { Component } from 'react';

const axios = require('axios');
const iconv = require('iconv-lite');

import { CSVReader } from 'react-papaparse';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
import ReactTooltip from 'react-tooltip';
import AutoSizer from 'react-virtualized-auto-sizer';
import { VariableSizeGrid as Grid } from 'react-window';
import logo from './logo-loader-white.svg';

import { generateTsv, pipelineById, resetPipeline, setLoading, Store } from './Models';

import { PendingFilesTableRow, PendingFilesTableError }  from './Pending-Files-Table-Row';
const Cell = ({ columnIndex, rowIndex, data, style }) => {

}

const ErrorCell = ({ columnIndex, rowIndex, data, style }) => {
  let item = '', errors, rowHasErrors = false;
  if (data && data[rowIndex] && data[rowIndex][columnIndex]) {
    item = data[rowIndex][columnIndex].data;
    errors = data[rowIndex][columnIndex].errors;
    rowHasErrors = data[rowIndex][columnIndex].rowHasErrors;
  }

  const lengthy = item && item.length > 144;
  const cellError = errors && errors.length > 0;
  let errorMessages = [];
  if (cellError) {
    // svg info icon source:
    // https://icons.getbootstrap.com/icons/info-circle-fill/
    // retrieved 2021-03-24
    for (let i = 0; i < errors.length; i++) {
      errorMessages.push(
        <div className="error-msg"
        key={`${rowIndex}-${columnIndex}-error-${i}`}>
          <a data-tip={errors[i]} data-for="error-cell-tooltips">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#900" className="bi bi-info-circle-fill" viewBox="0 0 16 16">
              <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412l-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>
            </svg>
          </a>
          <ReactTooltip id="error-cell-tooltips" place="right" type="dark" effect="solid"
          className="error-cell-tooltip" clickable={true}
          event={'click'} globalEventOff={'click'} />
        </div>
      )
    }
  }
  return (
    <div className={
      `${rowHasErrors ? 'GridError': ''} ${rowIndex % 2 === 0
        ? 'GridItemEven'
        : 'GridItemOdd'
        } ${lengthy
          ? 'GridItemLong'
          : ''
        } ${cellError
          ? 'CellError'
          : ''
        } GridColumn${columnIndex} GridRow${rowIndex} `
      }
      style={style}>
      <div className={'CellFrame'}>
        <div className={'GridCell'}>
          <p>{item}</p>
          {errorMessages}
        </div>
      </div>
    </div>
  )
}

class PendingFiles extends Component {
  constructor(props) {
    super(props)
    const introText = `This page hosts a newly (2021) developed
    in-browser file validator. <br />
    This validator aims to make it easier to
    submit files into the Vizor system.<br />
    <br />
    The in-browser validator can display all error messages at one time,<br />
    and provide details on the exact rows and cells which contain
    unexpected values. <br />
    Additionally, you can upload comma-separated values to this validator,<br />
     and it will handle conversion to the system-required <br />
     tab-separated values format for you.<br />
    <br />
    This feature is new, and the interface is quite different.<br />
    For maximum flexibility and compatibility,
    the original tooling is still available. <br />
    Use the "Legacy Upload Page"
    link below to access the old functionality.`

    const pipeline = pipelineById(props.ivetlPipelineId);
    let pendingFiles = [];
    if (props.ivetlPendingFiles) {
      try {
        let pf = JSON.parse(props.ivetlPendingFiles);
        if (Array.isArray(pf)) {
          pendingFiles = pf.filter((item) => {
            return typeof item.file_name !== 'undefined';
          })
        }
      }
      catch {
        console.log('invalid JSON supplied to pending files property, ignoring.');
        console.log(props.ivetlPendingFiles);
      }
    }

    if (props.ivetlLogoUrl) {
      this.logoUrl = props.ivetlLogoUrl;
    }
    else {
      this.logoUrl = logo;
    }

    this.state = {
      fileEncoding: null,
      fileValidated: false,
      loading: false,
      productId: props.ivetlProductId,
      pipelineId: props.ivetlPipelineId,
      pipelineName: pipeline.name,
      publisherId: props.ivetlPublisherId,
      pendingFilesBaseUrl: props.ivetlPendingFilesUrl,
      pendingFiles: pendingFiles,
      pendingFilesError: false,
      uploadUrl: props.ivetlUploadUrl,
      deleteUrl: props.ivetlDeleteUrl,
      isDemo: !props.ivetlIsDemo || props.ivetlIsDemo === 'false'
        ? false
        : props.ivetlIsDemo,
      csrfToken: props.ivetlCsrfToken,
      parsedRows: [],
      rows: [],
      rowCount: 0,
      rowErrors: [],
      textErrors: [],
      rowErrorsIndex: {},
      validator: pipeline.validator,
      validatorIntro: introText,
      columns: pipeline.fileColumns
    }
    this.fileRef = React.createRef()
    this.dataStore = new Store();
    this.onCsvLoadStart = this.onCsvLoadStart.bind(this);
    this.handleOnError = this.handleOnError.bind(this);
    this.handleData = this.handleData.bind(this);
    this.handleComplete = this.handleComplete.bind(this);
    this.submitFile = this.submitFile.bind(this);
    this.deleteFile = this.deleteFile.bind(this);
  }

  getPendingFiles = () => {
    let { pendingFilesBaseUrl, publisherId, productId, pipelineId } = this.state;

    const url = `${pendingFilesBaseUrl}${publisherId}/${productId}/${pipelineId}/pendingfiles`;
    return new Promise((resolve, reject) => {
      axios.get(url)
        .then((response) => {
          resolve(response.data.pendingFiles || []);
        })
        .catch((error) => {
          reject(error);
        })
    });
  }

  handleEncodingChange = (event) => {
    let encoding = this.state.fileEncoding;
    console.log(this.fileRef.current);
    if (event && event.target) {
      this.setState({
        fileEncoding: event.target.value
      })
    }
  }

  onCsvLoadStart = (e) => {
    console.log('onCsvLoadStart');
    setLoading(this.state.pipelineId, true);
    // this.setState({ loading: true });
  }

  handleOnError = (err, file, inputElem, reason) => {
    console.log(err)
    this.setState({
      loading: false
    });
  }

  handleOnRemoveFile = (data) => {
    console.log('---------------------------')
    console.log(data)
    console.log('---------------------------')
    resetPipeline(this.state.pipelineId);
    this.dataStore.reset();
    this.setState({
      fileValidated: false,
      parsedRows: [],
      rows: [],
      rowCount: 0,
      rowErrors: [],
      rowErrorsIndex: {},
      textErrors: []
    })
  }

  handleData = (results, parser) => {
    let parsedRows = this.dataStore.state.parsedRows;
    let rows = this.dataStore.state.rows;
    let rowCount = this.dataStore.state.rowCount;
    rowCount++;
    let rowErrors = this.dataStore.state.rowErrors;
    let textErrors = this.dataStore.state.textErrors;

    let val = this.state.validator(rowCount, results.data);
    val.rowCount = rowCount;
    if (!this.state.loading) {
      this.setState({ loading: true });
    }
    if (val.hasErrors ||
    (results.errors && results.errors.length > 0)) {
      val.parseErrors = results.errors;
      let errors = this.state.rowErrors;
      let errorIdx = this.state.rowErrorsIndex;
      errorIdx[`row_${rowCount}`] = val;

      if (val.row.length > 0) {
        val.row.forEach((rowLevelError) => {
          textErrors.push(`Row ${val.rowCount}: ${rowLevelError}`)
        });
      }
      val.data.forEach((column, idx) => {
        if (column.errors.length > 0) {
          column.errors.forEach((columnError) => {
            textErrors.push(`Row ${val.rowCount}, Column ${idx + 1}: ${columnError}`)
          });
        }
      });

      rowErrors.push(val.data);

    }
    parsedRows.push(results.data);
    rows.push(val.data);
    this.dataStore.state.rowCount = rowCount;
  }

  handleComplete = (results, file) => {
    // todo: check results for error / warn prior to allow submission

    // setTimeout gives more noticeable display of spinner for short files
    let newState = {
      ...this.dataStore.state,
      fileValidated: true,
      loading: false
    };
    console.log('parsing done');
    console.log(this.dataStore.state);
    setTimeout(() => {
      setLoading(this.state.pipeline_id, false);
      this.setState(newState);
      console.log('Parsing complete: ', results, file)
    }, 1000)


  }

  setFileEncoding = (event) => {

  }

  submitFile = (event) => {
    event.preventDefault();
    console.log('submit file request...');
    console.log(event.target);
    let c = this;
    let uploadUrl = c.state.uploadUrl;
    let csrf = c.state.csrfToken;
    let parsedRows = c.state.parsedRows;
    let filename;
    const withCredentials = c.props.axiosWithCredentials;

    if (c.fileRef.current && c.fileRef.current.fileNameInfoRef &&
    c.fileRef.current.fileNameInfoRef.current &&
    c.fileRef.current.fileNameInfoRef.current.innerHTML) {
        filename = c.fileRef.current.fileNameInfoRef.current.innerHTML;
    }
    else {
      filename = `${c.publisherId}_${c.product_id}_vizor_manager_upload.tsv`;
    }

    c.setState({ loading: true });
    console.log('file info: ', filename)
    generateTsv(parsedRows)
      .then((tsv) => {
        console.log('tsv generation success...');
        console.log(tsv.size * 0.001, ' kb');
        console.log(tsv.type);
        let submissionForm = new FormData(event.target);
        submissionForm.append('files', tsv, filename);
        console.log('created form...');
        console.log(submissionForm);
        for (let key of submissionForm.keys()) {
          console.log(key);
          console.log(submissionForm.getAll(key))
        }
        return axios({
          method: 'POST',
          url: uploadUrl,
          data: submissionForm,
          headers: {
            'Content-Type': 'multipart/form-data',
            'X-CSRFToken': csrf
          },
          responseType: 'text',
          xsrfCookieName: 'csrftoken',
          xsrfHeaderName: 'X-CSRFToken',
          withCredentials: withCredentials
        });
      })
      .then((response) => {
        console.log('upload success');
        console.log(response);
        let pending = c.state.pendingFiles;
        if (response && response.data &&
        Array.isArray(response.data.processed_files)) {
          c.setState({
            loading: false,
            pendingFiles: [ ...pending, ...response.data.processed_files ]
          })
        }
        else {
          // todo: message error response
          console.log('Unexpected (yet 2xx) response from file upload...')
          console.log(response);
          c.setState({
            loading: false
          });
        }
      })
      .catch((err) => {
        console.log('error generating tsv...');
        console.log(err);
        c.setState({ loading: false });
      })
  }

  deleteFile = (file) => {
    console.log('delete file');
    console.log(file);
    let c = this;
    const deleteUrl = c.state.deleteUrl;
    let reqData = [
      { name: 'csfrmiddlewaretoken', value: c.state.csfrtoken },
      { name: 'file_to_delete', value: file.file_name },
      { name: 'product_id', value: c.state.productId },
      { name: 'pipeline_id', value: c.state.pipelineId }
    ];

    if (c.state.isDemo) {
      reqData.push({ name: 'file_type', value: 'demo' });
      reqData.push({ name: 'demo_id', value: c.state.demoId });
    }
    else {
      reqData.push({ name: 'file_type', value: 'publisher' });
      reqData.push({ name: 'publisher_id', value: c.state.publisherId });
    }

    console.log(reqData);
    let reqForm = new FormData();
    for (let i = 0; i < reqData.length; i++) {
      reqForm.append(reqData[i].name, reqData[i].value);
    }
    c.setState({ loading: true });
    axios({
      method: 'POST',
      url: deleteUrl,
      data: reqForm,
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-CSRFToken': c.state.csrf
      },
      responseType: 'text',
      xsrfCookieName: 'csrftoken',
      xsrfHeaderName: 'X-CSRFToken',
      withCredentials: c.props.withCredentials
    })
    .then(() => {
      console.log('deleted file');
      let pendingFiles = c.state.pendingFiles.filter((item) => {
        return item.file_name !== file.file_name;
      });
      c.setState({
        loading: false,
        pendingFiles: [ ...pendingFiles ]
      })
    })
    .catch((err) => {
      // todo: message error to end user
      console.log('Error deleting file');
      console.log(err);
      c.setState({ loading: false });
    })
  }

  render() {
    let r = this;
    // Extending defaults found here:
    // https://github.com/Bunlong/react-papaparse/blob/master/src/CSVReader.tsx
    // 'text/csv' for MacOS
    // '.csv' for Linux
    // 'application/vnd.ms-excel' for Window 10
    // We are guessing delimiters and doing our own validation client-side,
    // so the file system extension or perceived mime type is not as much of a concern.
    const DEFAULT_ACCEPT = 'text/csv, .csv, application/vnd.ms-excel';
    const TAB_ACCEPT = 'text/tsv, .tsv, .tab, tab-separated-values';
    const ACCEPT = 'text/plain, .txt';
    const successColor = '#449966';
    const errorColor = '#994422';
    let papaParseConfig = {
      worker: true,
      step: r.handleData,
      complete: r.handleComplete,
      encoding: r.state.fileEncoding || 'UTF-8'
    };
    let csvElem = r.state.fileEncoding
      ? (
          <CSVReader
            config={papaParseConfig}
            onError={r.handleOnError}
            onLoadStart={r.onCsvLoadStart}
            accept={`${DEFAULT_ACCEPT} ${TAB_ACCEPT} ${ACCEPT}`}
            addRemoveButton
            onRemoveFile={r.handleOnRemoveFile}
            noProgressBar={true}
            ref={r.fileRef}
            className="react-papaparse-csv-reader"
          >
            <span>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            Drop file here
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;

            <br />
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            or click to upload.
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>
            {/* non-breaking spaces above are just a hack to keep the
              bounding box a similar size on change, so the UI is less jumpy */}
          </CSVReader>
        )
      : (
        <div>
          <input type="file"
          accept="text/csv, .csv, application/vnd.ms-excel text/tsv, .tsv, .tab, tab-separated-values text/plain, .txt"
          disabled={true}
          style={{display: 'none'}} />
          <div className="csv-specify-encoding-cta">
            <span>To validate, first select an &nbsp;&nbsp;<br />
encoding option to the left.</span>
          </div>
        </div>
      )

    // todo: consider refactoring pending files section into new component
    let pendingFilesDisplay = '';
    let pendingFilesTable = '', pendingFilesTableRows = [];
    if (r.state.pendingFiles.length > 0) {
      for (let i = 0; i < r.state.pendingFiles.length; i++) {
        pendingFilesTableRows.push(
          <PendingFilesTableRow file={r.state.pendingFiles[i]}
            cb={r.deleteFile}
            key={`PendingFilesTableRow-${i}`} />
        );
        if (r.state.pendingFiles[i].validation_errors &&
        r.state.pendingFiles[i].validation_errors.length > 0) {
          pendingFilesTableRows.push(
            <PendingFilesTableError file={r.state.pendingFiles[i]}
            key={`PendingFilesTableError-${i}`} />
          );
        }
      }

      pendingFilesTable = (
        <table className="table all-files-table has-files">
          <thead>
              <tr>
                  <th><span className="status-icon status-empty"></span></th>
                  <th>File</th>
                  <th>Lines</th>
                  <th>Size</th>
                  <th>Status</th>
                  <th></th>
              </tr>
          </thead>
          <tbody>
            { pendingFilesTableRows }
          </tbody>
        </table>
      )
      pendingFilesDisplay = (
        <div className="pending-files-container pending-files">
          { pendingFilesTable }
          <div className="file-submission">
            <form id="run-pipeline-for-publisher-form" className="form-horizontal"
            method="post" action={r.props.ivetlRunPipelineUrl}>
                <input type="hidden" name="csrfmiddlewaretoken" value={ r.state.csrfToken } />
                <input type="hidden" name="move_pending_files" value="1" />
                <input type="hidden" name="publisher" value={ r.state.publisherId } />
                <span>
                  <button className="btn btn-primary submit-button submit-for-processing-button"
                  type="submit" value="Submit"
                  disabled={r.state.pendingFiles.length < 1}>
                    Submit Validated Files for Processing
                  </button> or

                  <span className="cancel">
                  <a href="#">I'll submit them later
                  </a>
                  </span>
                </span>
            </form>
          </div>
        </div>
      )
    }
    let textErrors = r.state.textErrors;

    let textErrorItems = textErrors.map((textError, idx) => {
      return (
        <li className="text-error-item" key={`text-error-item-${idx}`}>{ textError }</li>
      )
    })

    return (
      <div className="pending-files">
        <div className="pending-files-header">
          <h4>In-Browser File Validator &nbsp;
            <a data-tip={r.state.validatorIntro} data-for="validator-info">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#359" className="bi bi-info-circle-fill" viewBox="0 0 16 16">
                <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412l-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>
              </svg>
            </a>
            <ReactTooltip id="validator-info" place="bottom" type="info" effect="solid"
            className="info-tooltip" event={'click'} globalEventOff={'click'}
            multiline={true}
            clickable={true} className="validator-intro" />
          </h4>
          <p>
            <i>The <a href={r.props.ivetlLegacyUploads}>
              Legacy Upload Page
            </a> remains available if preferred.
            </i>
          </p>
        </div>
        { pendingFilesDisplay }
        <div className="file-selection">
          <div className="file-upload-heading">
            <h4>Validate a New File</h4>
            <i>and display results in-browser</i>
          </div>
          <div className="file-encoding">
            <label className={`
              ${r.state.fileEncoding === 'UTF-8' ? 'active' : ''}
              ${r.state.rowCount > 0 ? 'disabled' : ''}
            `}>
              <input disabled={r.state.rowCount > 0} type="radio" value="UTF-8"
              checked={r.state.fileEncoding === 'UTF-8'}

              onChange={r.handleEncodingChange} />
              UTF-8
            </label>
            <br />
            <label className={`
              ${r.state.fileEncoding === 'ISO-8859-2' ? 'active' : ''}
              ${r.state.rowCount > 0 ? 'disabled' : ''}
            `}>
              <input disabled={true} type="radio" value="ISO-8859-2"
              checked={r.state.fileEncoding === 'ISO-8859-2'}
              onChange={r.handleEncodingChange} />
              ISO-8859-2 &nbsp;
              <a data-for="encoding-warning" data-tip={`Currently only UTF-8
                Encoding is supported. <br />
                  Additional encoding support will be added in a future release.
                `} className="encoding-warning"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-exclamation-circle-fill" viewBox="0 0 16 16">
                <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8 4a.905.905 0 0 0-.9.995l.35 3.507a.552.552 0 0 0 1.1 0l.35-3.507A.905.905 0 0 0 8 4zm.002 6a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>
                  </svg>
              </a>
            </label>
            <ReactTooltip id="encoding-warning" place="bottom" type="error" effect="solid"
            className="danger-tooltip" event={'click'} globalEventOff={'click'}
            multiline={true}
            clickable={true} className="encoding-warning" />
          </div>
          <div className="loader-frame">
            <img className={`hwp-loading-icon ${r.state.loading
              ? '' : 'not-loading'}`} src={this.logoUrl} alt="loading..." />
          </div>
          <div className="csv-frame">
            {csvElem}
          </div>
          <div className="validated-file-upload">
            <form onSubmit={r.submitFile} method="post" encType="multipart/form-data">
                <input type="hidden" name="csrfmiddlewaretoken" value={ r.state.csrfToken } />
                <input type="hidden" name="product_id" value={ r.state.productId } />
                <input type="hidden" name="pipeline_id" value={ r.state.pipelineId } />
                <input type="hidden" name="client_validated" value="1" />
                <input type="hidden" name="file_type" value="publisher" />
                <input type="hidden" name="publisher_id" value={ r.state.publisherId } />

                <button className="btn btn-info" disabled={!r.state.fileValidated}
                type="submit" value="Submit">
                  Upload validated file
                </button>
            </form>

          </div>
        </div>
        <div className="result-view">
          <Tabs>
            <TabList>
              <Tab>
                <span title="Error rows - Spreadsheet view">
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                  <svg xmlns="http://www.w3.org/2000/svg" className="bi bi-bug" width="16" height="16" fill={errorColor} viewBox="0 0 16 16">
                    <path d="M4.355.522a.5.5 0 0 1 .623.333l.291.956A4.979 4.979 0 0 1 8 1c1.007 0 1.946.298 2.731.811l.29-.956a.5.5 0 1 1 .957.29l-.41 1.352A4.985 4.985 0 0 1 13 6h.5a.5.5 0 0 0 .5-.5V5a.5.5 0 0 1 1 0v.5A1.5 1.5 0 0 1 13.5 7H13v1h1.5a.5.5 0 0 1 0 1H13v1h.5a1.5 1.5 0 0 1 1.5 1.5v.5a.5.5 0 1 1-1 0v-.5a.5.5 0 0 0-.5-.5H13a5 5 0 0 1-10 0h-.5a.5.5 0 0 0-.5.5v.5a.5.5 0 1 1-1 0v-.5A1.5 1.5 0 0 1 2.5 10H3V9H1.5a.5.5 0 0 1 0-1H3V7h-.5A1.5 1.5 0 0 1 1 5.5V5a.5.5 0 0 1 1 0v.5a.5.5 0 0 0 .5.5H3c0-1.364.547-2.601 1.432-3.503l-.41-1.352a.5.5 0 0 1 .333-.623zM4 7v4a4 4 0 0 0 3.5 3.97V7H4zm4.5 0v7.97A4 4 0 0 0 12 11V7H8.5zM12 6a3.989 3.989 0 0 0-1.334-2.982A3.983 3.983 0 0 0 8 2a3.983 3.983 0 0 0-2.667 1.018A3.989 3.989 0 0 0 4 6h8z"/>
                  </svg>
                  &nbsp;
                  <svg xmlns="http://www.w3.org/2000/svg" className="bi bi-grid-3x3" width="16" height="16" fill={errorColor} viewBox="0 0 16 16">
                    <path d="M0 1.5A1.5 1.5 0 0 1 1.5 0h13A1.5 1.5 0 0 1 16 1.5v13a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 0 14.5v-13zM1.5 1a.5.5 0 0 0-.5.5V5h4V1H1.5zM5 6H1v4h4V6zm1 4h4V6H6v4zm-1 1H1v3.5a.5.5 0 0 0 .5.5H5v-4zm1 0v4h4v-4H6zm5 0v4h3.5a.5.5 0 0 0 .5-.5V11h-4zm0-1h4V6h-4v4zm0-5h4V1.5a.5.5 0 0 0-.5-.5H11v4zm-1 0V1H6v4h4z"/>
                  </svg>
                  &nbsp;&nbsp;&nbsp;&nbsp;
                </span>
              </Tab>
              <Tab>
                <span title="Errors - Text summary">
                &nbsp;&nbsp;&nbsp;&nbsp;
                  <svg xmlns="http://www.w3.org/2000/svg" className="bi bi-bug" width="16" height="16" fill={errorColor} viewBox="0 0 16 16">
                    <path d="M4.355.522a.5.5 0 0 1 .623.333l.291.956A4.979 4.979 0 0 1 8 1c1.007 0 1.946.298 2.731.811l.29-.956a.5.5 0 1 1 .957.29l-.41 1.352A4.985 4.985 0 0 1 13 6h.5a.5.5 0 0 0 .5-.5V5a.5.5 0 0 1 1 0v.5A1.5 1.5 0 0 1 13.5 7H13v1h1.5a.5.5 0 0 1 0 1H13v1h.5a1.5 1.5 0 0 1 1.5 1.5v.5a.5.5 0 1 1-1 0v-.5a.5.5 0 0 0-.5-.5H13a5 5 0 0 1-10 0h-.5a.5.5 0 0 0-.5.5v.5a.5.5 0 1 1-1 0v-.5A1.5 1.5 0 0 1 2.5 10H3V9H1.5a.5.5 0 0 1 0-1H3V7h-.5A1.5 1.5 0 0 1 1 5.5V5a.5.5 0 0 1 1 0v.5a.5.5 0 0 0 .5.5H3c0-1.364.547-2.601 1.432-3.503l-.41-1.352a.5.5 0 0 1 .333-.623zM4 7v4a4 4 0 0 0 3.5 3.97V7H4zm4.5 0v7.97A4 4 0 0 0 12 11V7H8.5zM12 6a3.989 3.989 0 0 0-1.334-2.982A3.983 3.983 0 0 0 8 2a3.983 3.983 0 0 0-2.667 1.018A3.989 3.989 0 0 0 4 6h8z"/>
                  </svg>
                  &nbsp;
                  <svg xmlns="http://www.w3.org/2000/svg" className="bi bi-layout-text-window-reverse" width="16" height="16" fill={errorColor} viewBox="0 0 16 16">
                    <path d="M13 6.5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h5a.5.5 0 0 0 .5-.5zm0 3a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h5a.5.5 0 0 0 .5-.5zm-.5 2.5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1 0-1h5z"/>
                    <path d="M14 0a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h12zM2 1a1 1 0 0 0-1 1v1h14V2a1 1 0 0 0-1-1H2zM1 4v10a1 1 0 0 0 1 1h2V4H1zm4 0v11h9a1 1 0 0 0 1-1V4H5z"/>
                  </svg>
                  &nbsp;&nbsp;&nbsp;&nbsp;
                </span>
              </Tab>
              <Tab>
                <span title="Full Validated Results">
                &nbsp;&nbsp;&nbsp;&nbsp;
                  <svg xmlns="http://www.w3.org/2000/svg" className="bi bi-check-all" width="16" height="16" fill={successColor} viewBox="0 0 16 16">
                    <path d="M8.97 4.97a.75.75 0 0 1 1.071 1.05l-3.992 4.99a.75.75 0 0 1-1.08.02L2.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093L8.95 4.992a.252.252 0 0 1 .02-.022zm-.92 5.14l.92.92a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 1 0-1.091-1.028L9.477 9.417l-.485-.486-.943 1.179z"/>
                  </svg>
                  &nbsp;
                  <svg xmlns="http://www.w3.org/2000/svg" className="bi bi-grid-3x3" width="16" height="16" fill={successColor} viewBox="0 0 16 16">
                    <path d="M0 1.5A1.5 1.5 0 0 1 1.5 0h13A1.5 1.5 0 0 1 16 1.5v13a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 0 14.5v-13zM1.5 1a.5.5 0 0 0-.5.5V5h4V1H1.5zM5 6H1v4h4V6zm1 4h4V6H6v4zm-1 1H1v3.5a.5.5 0 0 0 .5.5H5v-4zm1 0v4h4v-4H6zm5 0v4h3.5a.5.5 0 0 0 .5-.5V11h-4zm0-1h4V6h-4v4zm0-5h4V1.5a.5.5 0 0 0-.5-.5H11v4zm-1 0V1H6v4h4z"/>
                  </svg>
                  &nbsp;&nbsp;&nbsp;&nbsp;
                </span>
              </Tab>
            </TabList>

            <TabPanel>
              <h3>Errors - Spreadsheet View</h3>
              <p><i>Rows containing errors are displayed here,
              with erroroneous cells highlighted
              </i>
              </p>
              <AutoSizer>
                {({ height, width }) => (
                  <Grid
                    className="Grid"
                    columnCount={r.state.columns.length}
                    columnWidth={index => r.state.columns[index].px || 100}
                    height={height > 800 ? height : 800}
                    itemData={r.state.rowErrors}
                    rowCount={r.state.rowErrors.length}
                    rowHeight={index => 150}
                    width={width}
                  >
                    {ErrorCell}
                  </Grid>
                )}
              </AutoSizer>
            </TabPanel>
            <TabPanel>
              <h3>Errors - Text Summary</h3>
              <p><i>Text summary of all errors, with row numbers.
              Total: { textErrorItems.length }</i></p>

              <div>
                <ul className="text-error-summary">
                  { textErrorItems }
                </ul>
              </div>
            </TabPanel>
            <TabPanel>
              <h3>Full Spreadsheet</h3>
              <p><i>All parsed rows are available on this tab for review.</i></p>
              <AutoSizer>
                {({ height, width }) => (
                  <Grid
                    className="Grid"
                    columnCount={r.state.columns.length}
                    columnWidth={index => r.state.columns[index].px || 100}
                    height={height > 800 ? height : 800}
                    itemData={r.state.rows}
                    rowCount={r.state.rows.length}
                    rowHeight={index => 150}
                    width={width}
                  >
                    {ErrorCell}
                  </Grid>
                )}
              </AutoSizer>
            </TabPanel>
          </Tabs>
        </div>
      </div>
    )
  }
}

PendingFiles.defaultProps = {
  isDemo: false,
  axiosWithCredentials: false,
  csrfToken: '',
  parsedRows: [],
  rows: [],
  columns: []
};

export default PendingFiles;
