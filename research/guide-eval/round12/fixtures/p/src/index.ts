// A tiny blog backend. Storage is in memory for now; we want a real database.
type Post = { id: number; title: string; content?: string; published: boolean; authorEmail: string };

const posts: Post[] = [];

export function addPost(p: Omit<Post, "id">): Post {
  const post = { ...p, id: posts.length + 1 };
  posts.push(post);
  return post;
}

console.log("notes-api ready");
