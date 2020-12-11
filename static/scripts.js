const endDate = '2021-01-05'

const today = new Date(); 

const diffInMs = new Date(endDate) - new Date(today);
const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

document.getElementById('countdown').innerHTML = 'Runoff elections are all about turnout: we have <strong>' + diffInDays + ' days</strong> left to make sure every Georgia voter can make their voice heard.';
