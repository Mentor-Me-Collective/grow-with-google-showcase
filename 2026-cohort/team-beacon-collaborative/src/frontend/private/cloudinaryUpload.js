const CLOUDINARY_CLOUD_NAME = "kn8f4ozi";
const CLOUDINARY_UPLOAD_PRESET = "nourish_share_profiles";
const MAX_PROFILE_IMAGE_BYTES = 5 * 1024 * 1024;

export async function uploadProfileImage(file) {
  if (!file) {
    throw new Error("Please choose an image.");
  }

  if (!file.type.startsWith("image/")) {
    throw new Error("Profile photo must be an image.");
  }

  if (file.size > MAX_PROFILE_IMAGE_BYTES) {
    throw new Error("Profile photo must be 5 MB or smaller.");
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("upload_preset", CLOUDINARY_UPLOAD_PRESET);

  const response = await fetch(
    `https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/image/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  const result = await response.json();

  if (!response.ok || !result.secure_url) {
    throw new Error(
      result?.error?.message || "Profile photo upload failed."
    );
  }

  return result.secure_url;
}
