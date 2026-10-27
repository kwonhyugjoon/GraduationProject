"""Camera-only queries protect decorative surfaces without blocking the player."""
import unreal

def configure_architecture_collision(component,solid):
    component.set_collision_profile_name('BlockAll' if solid else 'MuseumCameraOnly')
