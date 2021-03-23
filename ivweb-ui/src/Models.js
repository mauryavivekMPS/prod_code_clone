const pipelines = {
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
    rowValidator: function (idx, row) {

    }
  }
}

export function pipelineById(pipelineId) {
  if (typeof pipelines[pipelineId] !== 'undefined') {
    return pipelines[pipelineId];
  }
  else {
    console.log('Failed to match supplied pipelineId in model:');
    console.log(pipelineId);
    return {
      id: '',
      name: 'Error - pipeline not configured',
      fileColumns: [],
      validator: function (row) {}
    }
  }
}
