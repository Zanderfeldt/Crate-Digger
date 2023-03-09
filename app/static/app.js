// MUSIC RECOMMENDATION SEARCH FUNCTIONS ---------------------
const $search = $('#artist_search')
const $search_results = $('#artist_search_results')
const $search_btn = $('#artist_search_button')
const $submit = $('#seed_submit_button')

$search_btn.on("click", async function(e) {
  
  e.preventDefault();

  $('#not_found_alert').remove();

  const id = await getId($('#name').val(), $('input[name="input_type"]:checked').val())

  //renders the content for an ARTIST search
  if (id.data.input_type == 'artist') {

    //displays message if artist is not found
    if (id.data.artists.total == 0) {
      message = '<div id="not_found_alert" class="alert alert-warning mt-4" role="alert">Artist not found</div>'
      $search.append(message);
    }
    for (result of id.data.artists.items) {
      link = `<input type="checkbox" name="${id.data.input_type}" value="${result.id}" id="${result.name}" class="btn-check"><label class="btn btn-outline-success btn-sm m-2" for="${result.name}">${result.name}</label>`
      $search_results.append(link);
    }
  }
  
  //renders the content for a TRACK search
  if (id.data.input_type == 'track') {

    //displays message if track is not found
    if (id.data.tracks.total == 0) {
      message = '<div id="not_found_alert" class="alert alert-warning mt-4" role="alert">Track not found</div>'
      $search.append(message);
    }
    for (result of id.data.tracks.items) {
      link = `<input type="checkbox" name="${id.data.input_type}" value="${result.id}" id="${result.name}" class="btn-check"><label class="btn btn-outline-success btn-sm m-2" for="${result.name}">${result.name} by ${result.artists[0].name}</label>`
      $search_results.append(link);
    }
  }

  //reset/clear text search input
  $('#name').val('');
})

// Calls artist/track search and returns Spotify specific IDs for use in final payload of main search

async function getId(name, type) {

  resp = await axios.get('/search', {
    params: {
      q: name,
      type: type
  }
 })
 return resp
}
