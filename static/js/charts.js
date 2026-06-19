const categoryCtx =
document.getElementById("categoryChart");

if(categoryCtx){

new Chart(categoryCtx,{

type:"pie",

data:{

labels:[
"Food",
"Shopping",
"Travel",
"Bills"
],

datasets:[{

data:[
35,
25,
20,
20
]

}]

}

});

}

const monthlyCtx =
document.getElementById("monthlyChart");

if(monthlyCtx){

new Chart(monthlyCtx,{

type:"bar",

data:{

labels:[
"Jan",
"Feb",
"Mar",
"Apr",
"May",
"Jun"
],

datasets:[{

label:"Expenses",

data:[
5000,
7000,
4000,
8000,
6500,
9000
]

}]

}

});

}
