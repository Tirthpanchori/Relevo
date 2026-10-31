export const repository = 'https://github.com/Tirthpanchori/Relevo';
export const asset = (path = '') => `${import.meta.env.BASE_URL}${path.replace(/^\//, '')}`;
export const page = (path = '') => asset(path);
export const source = path => `${repository}/blob/main/${path}`;

export function currentPage(pathname = window.location.pathname) {
  const base = import.meta.env.BASE_URL;
  const relative = pathname.startsWith(base) ? pathname.slice(base.length) : pathname.replace(/^\//, '');
  const slug = relative.replace(/(?:\/)?index\.html$/, '').replace(/^\/|\/$/g, '');
  return ['engine', 'results', 'docs', 'about', 'privacy'].includes(slug) ? slug : slug === '' ? 'home' : '404';
}
