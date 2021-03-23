import './Pending-Files.css';
import React, { Component } from 'react';

import { CSVReader } from 'react-papaparse';
import AutoSizer from 'react-virtualized-auto-sizer';
import { VariableSizeGrid as Grid } from 'react-window';
import { pipelineById } from './Models';

const Cell = ({ columnIndex, rowIndex, data, style }) => {
  let item = data && data[rowIndex] && data[rowIndex][columnIndex]
    ? data[rowIndex][columnIndex]
    : `col: ${columnIndex}, row: ${rowIndex}`;
  const lengthy = item && item.length > 144;
  return (
    <div className={
      `${rowIndex % 2 === 0
        ? 'GridItemEven'
        : 'GridItemOdd'
        } ${lengthy
            ? 'GridItemLong'
            : ''
        } GridColumn${columnIndex} GridRow${rowIndex} `
      }
      style={style}>
      <div className={'GridCell'}>{item}</div>
    </div>
  )
}

class PendingFiles extends Component {
  constructor(props) {
    super(props)
    const pipeline = pipelineById(props.ivetlPipelineId);
    this.state = {
      productId: props.ivetlProductId,
      pipelineId: props.ivetlPipelineId,
      publisherId: props.ivetlPublisherId,
      uploadUrl: props.ivetlUploadUrl,
      deleteUrl: props.ivetlDeleteUrl,
      isDemo: !props.ivetlIsDemo || props.ivetlIsDemo === 'false'
        ? false
        : props.ivetlIsDemo,
      csrfToken: props.ivetlCsrfToken,
      rows: [],
      validator: pipeline.validator,
      columns: pipeline.fileColumns
    }
    this.handleData = this.handleData.bind(this);
    this.handleComplete = this.handleComplete.bind(this);
    console.log('Initialized PendingFiles:');
    console.log(this.state);
  }
  handleOnDrop = (data) => {
    console.log('onDrop');
    console.log(data);
    return;
    const rows = this.state.rows;
    console.log('---------------------------')
    console.log(data)
    console.log('---------------------------')
    let mappedData = data.map((elem) => {
      return elem.data;
    })
    this.setState({
      rows: [...rows, ...mappedData]
    })
  }

  handleOnError = (err, file, inputElem, reason) => {
    console.log(err)
  }

  handleOnRemoveFile = (data) => {
    console.log('---------------------------')
    console.log(data)
    console.log('---------------------------')
  }

  handleData = (results, parser) => {
    const rows = this.state.rows;
    console.log('data...---------------------------')
    console.log(results)
    console.log('data...---------------------------')
    this.setState({
      rows: [...rows, results.data]
    })
  }

  handleComplete = (results, file) => {
    console.log('Parsing complete: ', results, file)
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
    const ACCEPT = 'text/plain, .txt'
    let papaParseConfig = {
      worker: true,
      step: r.handleData,
      complete: r.handleComplete
    };

    return (
      <div className="pending-files">
        <div className="file-selection">
          <span>Select one or more files to upload: </span>
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
        </div>
        <AutoSizer>
          {({ height, width }) => (
            <Grid
              className="Grid"
              columnCount={16}
              columnWidth={index => r.state.columns[index].px || 100}
              height={height > 1000 ? height : 1000}
              itemData={r.state.rows}
              rowCount={r.state.rows.length}
              rowHeight={index => 100}
              width={width}
            >
              {Cell}
            </Grid>
          )}
        </AutoSizer>
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
  rows: [],
  columns: []
};

export default PendingFiles;
