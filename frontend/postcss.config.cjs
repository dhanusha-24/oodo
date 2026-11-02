import tailwindcss from 'tailwindcss';
import autoprefixer from 'autoprefixer';
css: {
  postcss: {
    plugins: [
      tailwindcss(),
      autoprefixer(),
      ],
    },
},
