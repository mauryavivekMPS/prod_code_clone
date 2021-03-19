import './Pending-Files.css';
import React, { Component } from 'react'

import { CSVReader } from 'react-papaparse'
import AutoSizer from 'react-virtualized-auto-sizer';
import { VariableSizeGrid as Grid } from 'react-window';

let csvData = [];

const Cell = ({ columnIndex, rowIndex, data, style }) => {
  console.log('Cell...')
  console.log(data)
  let item = data && data[rowIndex] && data[rowIndex][columnIndex]
    ? data[rowIndex][columnIndex]
    : `col: ${columnIndex}, row: ${rowIndex}`;
  const lengthy = item && item.length > 144;
  return (
    <div className={
      `${columnIndex % 2
        ?  rowIndex % 2 === 0
          ? 'GridItemOdd'
          : 'GridItemEven'
        : rowIndex % 2
          ? 'GridItemOdd'
          : 'GridItemEven'} ${lengthy
            ? 'GridItemLong'
            : ''
          } GridColumn${columnIndex} GridRow${rowIndex} `
      }
      style={style}>
      <div className={'GridCell'}>{item}</div>
    </div>
  )
}

export default class PendingFiles extends Component {
  constructor(props) {
    super(props)
    this.state = {
      rows: [],
      columns: [
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
        },
      ]
    }
  }
  handleOnDrop = (data) => {
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

  render() {
    let r = this;
    return (
      <div className="pending-files">
        <div className="file-selection">
          <h1>Upload Rejected</h1>
          <CSVReader
            onDrop={this.handleOnDrop}
            onError={this.handleOnError}
            addRemoveButton
            onRemoveFile={this.handleOnRemoveFile}
          >
            <span>Drop CSV file here or click to upload.</span>
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
