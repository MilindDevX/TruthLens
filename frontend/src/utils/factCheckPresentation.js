export function factCheckPresentation(result = {}) {
  if (result.status === 'matched') {
    return {
      tone: 'positive',
      title: 'Published fact-check found',
      detail: `${result.publisher || 'A publisher'} rated a related claim “${result.rating || 'Unrated'}”.`,
      linkLabel: 'Open source',
      url: result.url,
    };
  }

  if (result.status === 'not_found') {
    return {
      tone: 'neutral',
      title: 'No published fact-check found',
      detail: 'No published review matched this text. This does not establish that it is true or false.',
    };
  }

  return {
    tone: 'warning',
    title: 'Fact-check lookup unavailable',
    detail: 'The model result above is not external evidence. Try again later.',
  };
}
