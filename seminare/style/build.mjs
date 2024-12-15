import * as esbuild from 'esbuild'
import {stimulusPlugin} from "esbuild-plugin-stimulus";

let options = {
    plugins: [stimulusPlugin()],
    entryPoints: ['seminare/style/js/app.js'],
    bundle: true,
    minify: true,
    outfile: 'seminare/style/static/app.min.js',
}

if (process.argv.indexOf('watch') !== -1) {
    let ctx = await esbuild.context(options)
    await ctx.watch()
} else {
    await esbuild.build(options)
}
