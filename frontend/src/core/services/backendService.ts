export async function checkBackendHealth() {

    try {

        const response = await fetch(
            `${import.meta.env.VITE_API_BASE_URL}/health`
        )

        return response.ok

    } catch {

        return false
    }
}