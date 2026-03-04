const getCookie = (name) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
};

let csrfRequestPromise = null;

export const getCsrfToken = () => getCookie("csrftoken");

export const ensureCsrfCookie = async (baseUrl) => {
  if (getCsrfToken()) return;
  if (!csrfRequestPromise) {
    csrfRequestPromise = fetch(`${baseUrl}/csrf/`, {
      method: "GET",
      credentials: "include",
    }).finally(() => {
      csrfRequestPromise = null;
    });
  }
  await csrfRequestPromise;
};
