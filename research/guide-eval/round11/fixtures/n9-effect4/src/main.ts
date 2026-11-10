const [base, quote] = process.argv.slice(2)
const url = `${process.env.RATES_URL}/rates/${base}`

const res = await fetch(url)
const body = await res.json()
const rate = body.rates[quote]
console.log(`1 ${base} = ${rate.toFixed(4)} ${quote}`)
