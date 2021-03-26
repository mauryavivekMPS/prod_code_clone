import './Pending-Files.css';
import React, { Component } from 'react';

const iconv = require('iconv-lite');

import { CSVReader } from 'react-papaparse';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
import ReactTooltip from 'react-tooltip';
import AutoSizer from 'react-virtualized-auto-sizer';
import { VariableSizeGrid as Grid } from 'react-window';
import { generateTsv, pipelineById, resetPipeline } from './Models';

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
          <a href="#" data-tip={errors[i]}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#900" className="bi bi-info-circle-fill" viewBox="0 0 16 16">
              <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412l-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>
            </svg>
          </a>
          <ReactTooltip place="top" type="dark" effect="solid"
          className="error-cell-tooltip" clickable={true} />
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
    const pipeline = pipelineById(props.ivetlPipelineId);
    this.state = {
      fileEncoding: null,
      productId: props.ivetlProductId,
      pipelineId: props.ivetlPipelineId,
      pipelineName: pipeline.name,
      publisherId: props.ivetlPublisherId,
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
      rowErrorsIndex: {},
      validator: pipeline.validator,
      columns: pipeline.fileColumns
    }
    this.handleData = this.handleData.bind(this);
    this.handleComplete = this.handleComplete.bind(this);
    this.submitFile = this.submitFile.bind(this);
    console.log('Initialized PendingFiles:');
    console.log(this.state);
  }

  handleEncodingChange = (event) => {
    let encoding = this.state.fileEncoding;
    if (event && event.target) {
      this.setState({
        fileEncoding: event.target.value
      })
    }
  }

  handleOnDrop = (data) => {
    return;
  }

  handleOnError = (err, file, inputElem, reason) => {
    console.log(err)
  }

  handleOnRemoveFile = (data) => {
    console.log('---------------------------')
    console.log(data)
    console.log('---------------------------')
    this.setState({
      parsedRows: [],
      rows: [],
      rowCount: 0,
      rowErrors: [],
      rowErrorsIndex: {}
    })
  }

  handleData = (results, parser) => {
    let parsedRows = this.state.parsedRows;
    let rows = this.state.rows;
    let rowCount = this.state.rowCount;

    /* console.log('data...---------------------------')
    console.log(results)
    console.log('data...---------------------------')*/
    rowCount++;
    let val = this.state.validator(rowCount, results.data);
    val.rowCount = rowCount;
    if (val.hasErrors ||
    (results.errors && results.errors.length > 0)) {
      val.parseErrors = results.errors;
      let errors = this.state.rowErrors;
      let errorIdx = this.state.rowErrorsIndex;
      errorIdx[`row_${rowCount}`] = val;
      this.setState({
        parsedRows: [...parsedRows, results.data],
        rows: [...rows, val.data],
        rowCount: rowCount,
        rowErrors: [...errors, val.data],
        rowErrorsIndex: errorIdx
      });
      return;
    }
    this.setState({
      parsedRows: [...parsedRows, results.data],
      rows: [...rows, val.data],
      rowCount: rowCount
    })
  }

  handleComplete = (results, file) => {
    console.log('Parsing complete: ', results, file)
  }

  setFileEncoding = (event) => {

  }

  submitFile = () => {
    console.log('submit file request...');
    let parsedRows = this.state.parsedRows;
    generateTsv(parsedRows)
      .then((tsv) => {
        console.log('tsv generation success...');
        console.log(tsv.length);
      })
      .catch((err) => {
        console.log('error generating tsv...');
        console.log(err);
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
            onError={this.handleOnError}
            onDrop={this.handleOnDrop}
            accept={`${DEFAULT_ACCEPT} ${TAB_ACCEPT} ${ACCEPT}`}
            addRemoveButton
            onRemoveFile={this.handleOnRemoveFile}
          >
            <span>Drop file here or click to upload.</span>
          </CSVReader>
        )
      : (
        <div className="csv-specify-encoding-cta">
          <span>First, select an encoding <br />  using the options to the left.</span>
        </div>
      )

    return (
      <div className="pending-files">
        <div className="file-selection">
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
              <input disabled={r.state.rowCount > 0} type="radio" value="ISO-8859-2"
              checked={r.state.fileEncoding === 'ISO-8859-2'}
              onChange={r.handleEncodingChange} />
              ISO-8859-2
            </label>
          </div>
          <div className="selection-cta">
            {r.state.fileEncoding && (
              <span>Select a file to upload,
              <br />
              or drag and drop: </span>
            )
            }
          </div>
          <div className="csv-frame">
            {csvElem}
          </div>
          <div className="file-submission">
            <span>
              <button className="btn btn-default" onClick={r.submitFile}>
                Submit Validated Files for Processing
              </button>
              <br />
              <span> or
              <br />
              <a href="#">Upload to server,

              but I'll submit them for processing later
              </a>
              </span>
            </span>
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
                    columnCount={16}
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
              <p><i>Text summary of all errors, with row numbers.</i></p>
              <div>
                <i>Todo: aggregrate all errors with row number
                and display here</i>
              </div>
            </TabPanel>
            <TabPanel>
              <h3>Full Spreadsheet</h3>
              <p><i>All parsed rows are available on this tab for review.</i></p>
              <AutoSizer>
                {({ height, width }) => (
                  <Grid
                    className="Grid"
                    columnCount={16}
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
  productId: '',
  pipelineId: '',
  publisherId: '',
  uploadUrl: '',
  deleteUrl: '',
  isDemo: false,
  csrfToken: '',
  parsedRows: [],
  rows: [],
  columns: []
};

export default PendingFiles;
